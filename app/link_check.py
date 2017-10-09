"""Recursive link checker"""
import argparse
import requests
from bs4 import BeautifulSoup
import datetime
from .globals import GET_TIMEOUT
from . import app, db, scheduler
from .models import Link, LinkCheck, ScanJob, ScheduledJob

def get_all_links(url):
    """Get all hrefs in the HTML of a given URL"""
    if is_flat_file(url):
        return []
    html = requests.get(url).content
    soup = BeautifulSoup(html, 'lxml')
    return [
        a['href'] for a in soup.find_all('a')
        if a.has_attr('href')]


def get_base_url(url):
    """Strip the scheme and trailing slashes from the URL"""
    url_root = '//'.join(url.split('//')[1:])
    url_stripped = url_root[:-1] if url_root.endswith('/') else url_root
    return url_stripped


def get_hostname(url):
    """strip the path and query string from the url"""
    url_root = '/'.join(url.split('/')[:3])
    url_stripped = url_root[:-1] if url_root.endswith('/') else url_root
    return url_stripped


def points_to_self(link, url_self):
    """Return true IFF `link` points to `url_self`"""
    if link == '/':
        return True
    if get_base_url(link) == get_base_url(url_self):
        return True
    return False


def is_internal_link(link, reference_url):
    """Return true IFF `link` is a sub-component of `reference_url`"""
    if link.startswith('/') or link.startswith('#'):
        return True
    if get_base_url(link).startswith(get_base_url(reference_url)):
        return True
    return False


def prepend_if_relative(link, url, keep_anchors=False):
    """Standardize `link` by prepending it with the hostname if relative"""
    if link.startswith('/'):
        return get_hostname(url) + link
    if link.startswith('#'):
        if keep_anchors:
            return url + link
        else:
            return url
    return link


def group_links_internal_external(links, url):
    """Split list `links` into internal and external links.
    Returns a tupple: (`internal_links`, `external_links`)
    """
    internal_links = []
    external_links = []
    for link in links:
        if is_internal_link(standardize_url(link), url):
            internal_links.append(prepend_if_relative(standardize_url(link), url))
        else:
            external_links.append(link)
    return internal_links, external_links


def is_flat_file(url):
    """Return True if `url` points to a (potentially large) flat file"""
    # strip url args:
    url = url.split('?')[0].split('#')[-1]

    splits = url.split('/')
    if len(splits) <= 3:
        return False

    ending = splits[-1]
    if '.' not in ending:
        return False

    file_type = ending.split('.')[-1]
    if file_type in ('html', 'htm', 'aspx', 'php', 'pdf', 'md', 'yml'):
        return False

    return True


def standardize_url(url):
    """Standardize `url` string formatting by removing anchors and trailing slashes,
    and by prepending schemas
    """
    if url.startswith('//'):
        url = 'http:' + url
    elif url.startswith('/') or url.startswith('#'):
        return url
    url = url.strip().split('#')[0].split('?')[0].replace('https://', 'http://')
    if url.endswith('/'):
        url = url[:-1]
    if not url.startswith('http') and not url.startswith('/'):
        url = 'http://' + url
    return url


class LinkChecker(object):
    """Link checker module, initialized with the root URL of the webiste to scan"""
    def __init__(self, url, user, owner=None):
        self.links_checked_and_followed = set()
        self.links_checked = []
        self.url = standardize_url(url)
        self.job = ScanJob(
            root_url=self.url,
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
        if link_standardized in self.links_checked:
            return
        elif is_flat_file(link):
            linkcheck_record = LinkCheck(
                **link_record_base,
                note='Flat file not checked'
            )
        else:
            try:
                response = requests.get(link_standardized, timeout=GET_TIMEOUT)
                note = None
                linkcheck_record = LinkCheck(
                    **link_record_base,
                    response=response.status_code,
                    text=response.text,
                )
            except Exception as exception:
                linkcheck_record = LinkCheck(
                    **link_record_base,
                    note=str(exception),
                )

        db.session.add(linkcheck_record)
        try:
            db.session.commit()
        except Exception as exception:
            # response text contains invalid string literals
            db.session.rollback()
            db.session.add(LinkCheck(
                **link_record_base,
                response=response.status_code,
                note=str(exception)))
            db.session.commit()

        self.links_checked.append(link_standardized)
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
        url_standardized = standardize_url(url)
        if url_standardized in self.links_checked_and_followed:
            return
        self.links_checked_and_followed.add(url_standardized)
        internal_links = self.check_all_links(url)
        for internal_link in internal_links:
            self.check_all_links_and_follow(internal_link)

    def get_errors(self, matcher):
        """Return a formatted JSON document describing any errors
        matching function `matcher`"""
        return LinkCheck.query.\
            filter(LinkCheck.job == self.job).\
            filter(matcher(LinkCheck.response))

    def report_errors(self, matcher):
        """Print any errors matching function `matcher`"""

        # get list of errors
        errors = self.get_errors(matcher)

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

        # print and return
        print(error_report)
        return error_report
