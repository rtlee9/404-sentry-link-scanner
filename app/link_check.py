"""Recursive link checker"""
import argparse
import requests
from requests.compat import urljoin, urlparse
from bs4 import BeautifulSoup
import datetime
from .globals import GET_TIMEOUT, PAGE_LIMIT
from . import app, db, scheduler
from .models import Link, LinkCheck, ScanJob, ScheduledJob


headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}


def get_all_links(url):
    """Get all hrefs in the HTML of a given URL"""
    if is_flat_file(url):
        return []
    try:
        response = requests.get(url, timeout=GET_TIMEOUT, verify=False, headers=headers)
    except requests.exceptions.RequestException as e:
        print('Error while getting links in {}'.format(url))
        print(e)
        return []
    html = response.content
    soup = BeautifulSoup(html, 'lxml')
    return [
        bytes(a['href'], "utf-8").decode("unicode_escape")
        for a in soup.find_all('a')
        if a.has_attr('href')]


def get_base_url(url):
    """Strip the scheme and trailing slashes from the URL"""
    if (url.startswith('http')) and ('//' in url):
        u = urlparse(url)
        url_root = u.netloc + u.path
    else:
        url_root = url
    url_stripped = url_root[:-1] if url_root.endswith('/') else url_root
    return url_stripped


def get_hostname(url):
    """strip the path and query string from the url"""
    u = urlparse(url)
    return '{}://{}'.format(u.scheme, u.hostname)


def points_to_self(link, url_self):
    """Return true IFF `link` points to `url_self`"""
    if link == '/':
        return True
    if get_base_url(link) == get_base_url(url_self):
        return True
    return False


def is_internal_link(link, reference_url):
    """Return true IFF `link` is a sub-component of `reference_url`"""
    if link.startswith('//'):
        return False
    if link.startswith('/') or link.startswith('#') or link.startswith('.'):
        return True
    if get_base_url(link).startswith(get_base_url(reference_url)):
        return True
    if '.' not in link.replace('.html', ''):
        return True
    return False


def ensure_protocol(url, protocol='http'):
    if urlparse(url).scheme:
        return url
    if url.startswith('javascript:') or url.startswith('mailto:'):
        return url
    if url.startswith('//'):
        return protocol + ':' + url
    return protocol + '://' + url


def prepend_if_relative(url, url_base, keep_anchors=False):
    """Standardize `url` by prepending it with the hostname if relative"""
    if url.startswith('javascript:') or url.startswith('mailto:'):
        return url
    url_joined = urljoin(standardize_url(url_base, True), url)
    if not keep_anchors:
        u = urlparse(url_joined)
        return '{}://{}{}'.format(u.scheme, u.netloc, u.path)
    return url_joined


def group_links_internal_external(links, url):
    """Split list `links` into internal and external links.
    Returns a tupple: (`internal_links`, `external_links`)
    """
    internal_links = []
    external_links = []
    for link in links:
        link = link.replace('"', '').replace("'", '')
        if is_internal_link(standardize_url(link), url):
            internal_links.append(prepend_if_relative(standardize_url(link), url))
        else:
            external_links.append(ensure_protocol(link.strip()))
    return internal_links, external_links


def is_flat_file(url):
    """Return True if `url` points to a (potentially large) flat file"""
    # strip url args:
    u = urlparse(url)
    url = '{}://{}{}'.format(u.scheme, u.netloc, u.path)
    if not u.path:
        return False

    if '.' not in u.path:
        return False

    file_type = u.path.split('.')[-1]
    if file_type in ('html', 'htm', 'aspx', 'php'):
        return False

    return True


def remove_trailing_slash(url):
    if url.endswith('/') and len(url) > 1:
        return url[:-1]
    return url


def standardize_url(url, keep_scheme=False):
    """Standardize `url` string formatting by removing anchors and trailing slashes,
    and by prepending schemas
    """

    # special case
    if url.startswith('javascript:') or url.startswith('mailto:'):
        return url

    # prepend scheme if necessary
    if url.startswith('//'):
        url = 'http:' + url
    elif '.' in urlparse(url).path.split('/')[-1] and not url.startswith('/'):
        url = ensure_protocol(url)

    # internal links
    u_dummy = urlparse(urljoin('http://dummy.com/dummy_path', url))
    if u_dummy.netloc == 'dummy.com':
        return remove_trailing_slash(url)

    # external links
    u = urlparse(ensure_protocol(url))
    scheme = u.scheme.replace('https', 'http') if not keep_scheme else u.scheme
    url = '{}://{}{}'.format(scheme, u.netloc, u.path).strip()
    return remove_trailing_slash(url)

def standardize_descheme_url(url):
    url_standardized = standardize_url(url)
    u = urlparse(ensure_protocol(url_standardized))
    return '{}{}'.format(u.netloc, u.path)


class LinkChecker(object):
    """Link checker module, initialized with the root URL of the webiste to scan"""
    def __init__(self, url, user, owner):
        self.links_checked_and_followed = set()
        self.url = ensure_protocol(standardize_url(url))
        self.job = ScanJob(
            root_url=standardize_descheme_url(self.url),
            start_time=datetime.datetime.utcnow(),
            user=user,
            status='in progress',
            owner=owner)
        db.session.add(self.job)
        db.session.commit()

    def check_link(self, link):
        """Request the resources specified by `link` and persist the results"""
        link_standardized = link
        link_record_base = dict(
            url_raw=link,
            url=link_standardized,
            job=self.job,
        )
        already_checked = LinkCheck.query.\
            filter(LinkCheck.job == self.job).\
            filter(LinkCheck.url == link_standardized).\
            count() > 0
        if already_checked:
            return
        else:
            try:
                response = requests.get(link_standardized, timeout=GET_TIMEOUT, stream=True, headers=headers)
                note = None
                linkcheck_record = LinkCheck(
                    **link_record_base,
                    response=response.status_code,
                )
                response.close()
            except Exception as exception:
                linkcheck_record = LinkCheck(
                    **link_record_base,
                    note=str(exception),
                    exception=type(exception).__name__,
                )

        db.session.add(linkcheck_record)
        db.session.commit()
        return linkcheck_record


    def check_links(self, links):
        """Check each link in array `links`"""
        for link in links:
            self.check_link(link)

    def check_all_links(self, url):
        """Find all links within `url` and check each one"""
        url_standardized = standardize_url(url)
        print('Checking all links found in {}'.format(url_standardized))
        links = get_all_links(url_standardized)
        _internal_links, external_links = group_links_internal_external(links, url_standardized)
        internal_links = []
        for internal_link in _internal_links:
            if internal_link.startswith(self.url):
                internal_links.append(internal_link)
            else:
                # link is above root so we don't want to scan it's children
                external_links.append(internal_link)

        # persist source links
        standardized_links = internal_links + external_links
        for link in standardized_links:
            link_record = Link(url=link, source_url=url_standardized, job=self.job)
            db.session.add(link_record)
        db.session.commit()

        # check links and return internal links for following
        self.check_links(internal_links)
        self.check_links(external_links)
        return internal_links

    def check_all_links_and_follow(self, url=None):
        """Recursively check all links in all sub-pages of `url`"""
        if url is None:
            url = self.url

        # break if page limit exceeded
        if len(self.links_checked_and_followed) > PAGE_LIMIT:
            print('Page limit {:,} exceeded for {}'.format(PAGE_LIMIT, url))
            return

        url_standardized = standardize_url(url)
        if url_standardized in self.links_checked_and_followed:
            return
        self.links_checked_and_followed.add(url_standardized)
        internal_links = self.check_all_links(url)
        for internal_link in internal_links:
            self.check_all_links_and_follow(internal_link)

    def get_results(self, matcher):
        """Return a formatted JSON document describing any errors
        matching function `matcher`"""
        return LinkCheck.query.\
            filter(LinkCheck.job == self.job).\
            filter(matcher(LinkCheck.response))

    def report_errors(self, matcher):
        """Print any errors matching function `matcher`"""

        # get list of errors
        errors = self.get_results(matcher)

        # get sources
        error_sources = Link.query.\
            filter(Link.url.in_(errors.with_entities(LinkCheck.url))).\
            filter(Link.job == self.job).\
            with_entities(Link.url, Link.source_url).all()

        # format sources > error mapping
        error_report = {}
        for error_source in error_sources:
            source_url = error_source.source_url
            url = error_source.url
            error_report[url] = error_report.get(url, []) + [source_url]

        return error_report
