from bs4 import BeautifulSoup
from requests import get, ConnectionError
from requests.sessions import InvalidSchema
import argparse


headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95'}
link_tree = {}
links_checked_and_followed = set()
links_checked = {}


def get_all_links(url):
    if is_flat_file(url):
        return []
    html = get(url).content
    soup = BeautifulSoup(html, 'lxml')
    return [a['href'] for a in soup.find_all('a') if a.has_attr('href')]


def test_get_all_links_len_8P():
    assert(len(get_all_links('http://eightportions.com')) > 15)


def get_base_url(url):
    url_root = '//'.join(url.split('//')[1:])
    url_stripped = url_root[:-1] if url_root.endswith('/') else url_root
    return url_stripped


def test_get_base_url():
    assert(get_base_url('https://eightportions.com') == 'eightportions.com')
    assert(get_base_url('http://eightportions.com') == 'eightportions.com')
    assert(get_base_url('http://eightportions.com/') == 'eightportions.com')
    assert(get_base_url('https://eightp//ortions.com') == 'eightp//ortions.com')


def get_hostname(url):
    url_root = '/'.join(url.split('/')[:3])
    url_stripped = url_root[:-1] if url_root.endswith('/') else url_root
    return url_stripped


def test_get_hostname():
    assert(get_hostname('https://eightportions.com') == 'https://eightportions.com')
    assert(get_hostname('http://eightportions.com') == 'http://eightportions.com')
    assert(get_hostname('http://eightportions.com/') == 'http://eightportions.com')
    assert(get_hostname('http://eightportions.com/asdf') == 'http://eightportions.com')
    assert(get_hostname('http://eightportions.com/asdf/dsf1') == 'http://eightportions.com')


def points_to_self(link, url_self):
    if link == '/':
        return True
    if get_base_url(link) == get_base_url(url_self):
        return True
    return False


def test_points_to_self():
    assert(points_to_self('/', 'asdf'))
    assert(points_to_self('https://eightportions.com', 'https://eightportions.com'))
    assert(points_to_self('http://eightportions.com', 'https://eightportions.com'))
    assert(points_to_self('http://eightpor//tions.com', 'https://eightpor//tions.com'))
    assert(~points_to_self('http://eightport//ions.com', 'https://eightpor//tions.com'))


def is_internal_link(link, reference_url):
    if link.startswith('/') or link.startswith('#'):
        return True
    if get_base_url(link).startswith(get_base_url(reference_url)):
        return True
    return False


def test_internal_link():
    assert(is_internal_link('/', 'https://eightportions.com'))
    assert(is_internal_link('/', 'asdfa'))
    assert(is_internal_link('https://eightportions.com', 'https://eightportions.com'))
    assert(~is_internal_link('https://eightportions.com', 'https://eightporasdf.com'))


def prepend_if_relative(link, url):
    if link.startswith('/') or link.startswith('#'):
        return get_hostname(url) + link
    else:
        return link


def test_prepend_if_relative():
    assert(prepend_if_relative('/', 'https://eightportions.com') == 'https://eightportions.com/')
    assert(prepend_if_relative('/page', 'https://eightportions.com') == 'https://eightportions.com/page')
    assert(prepend_if_relative('/page', 'http://eightportions.com') == 'http://eightportions.com/page')
    assert(prepend_if_relative('/page1/subpage1', 'http://eightportions.com') == 'http://eightportions.com/page1/subpage1')
    assert(prepend_if_relative('http://eightportions.com', 'http://eightportions.com') == 'http://eightportions.com')


def group_links_internal_external(links, url):
    internal_links = []
    external_links = []
    for link in links:
        if is_internal_link(link, url):
            internal_links.append(prepend_if_relative(link, url))
        else:
            external_links.append(link)
    return internal_links, external_links


def is_flat_file(url):
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


def test_is_flat_file():
    assert(not is_flat_file('http://eightportions.com'))
    assert(not is_flat_file('https://eightportions.com'))
    assert(not is_flat_file('https://eightportions.zip'))
    assert(is_flat_file('https://eightportions/test.zip'))
    assert(is_flat_file('https://eightportions/test.json'))
    assert(not is_flat_file('https://www.tensorflow.org/versions/r0.11/tutorials/wide_and_deep/index.html#tensorflow-wide-deep-learning-tutorial'))
    assert(not is_flat_file('http://www.informit.com/articles/article.aspx?p=2314818'))


def check_link(link):
    link_standardized = standardize_url(link)
    check_status = dict(
        url_raw=link,
        url=link_standardized,
    )
    if link_standardized in links_checked:
        return
    elif is_flat_file(link):
        check_status['note'] = 'Flat file not checked'
    else:
        try:
            response = get(link_standardized)
            check_status['response_status'] = response.status_code
            check_status['response_text'] = response.text
        except Exception as e:
            check_status['note'] = e
    links_checked[link_standardized] = check_status
    return check_status


def check_links(links):
    for link in links:
        check_link(link)


def standardize_url(url):
    url = url.strip().split('#')[0].split('?')[0]
    if url.endswith('/'):
        url = url[:-1]
    return url


def test_standardize_url():
    assert(standardize_url('https://eightportions.com ') == 'https://eightportions.com')
    assert(standardize_url('https://eightportions.com') == 'https://eightportions.com')
    assert(standardize_url('https://eightportions.com/ ') == 'https://eightportions.com')
    assert(standardize_url('https://eightportions.com/') == 'https://eightportions.com')
    assert(standardize_url('http://eightportions.com') == 'http://eightportions.com')
    assert(standardize_url('http://eightportions.com ') == 'http://eightportions.com')


def check_all_links(url):
    url_standardized = standardize_url(url)
    print('Checking all links found in {}'.format(url_standardized))
    links = get_all_links(url_standardized)
    link_tree[url_standardized] = [link for link in links if not is_internal_link(link, url_standardized)]
    internal_links, external_links = group_links_internal_external(links, url_standardized)

    # check links and return internal links for following
    check_links(internal_links)
    check_links(external_links)
    return internal_links


def check_all_links_and_follow(url):
    url_standardized = standardize_url(url)
    if url_standardized in links_checked_and_followed:
        return
    links_checked_and_followed.add(url_standardized)
    internal_links = check_all_links(url_standardized)
    for internal_link in internal_links:
        check_all_links_and_follow(internal_link)


def test_links_checked_and_followed():
    reset_inits()
    check_all_links_and_follow(' https://eightportions.com/img/Taxi_pick_by_drop.gif')
    assert(links_checked == {})
    assert(check_link('https://storage.googleapis.com/recipe-box/recipes_raw.zip')['note'] == 'Flat file not checked')


def reset_inits():
    links_checked = {}
    link_tree = {}
    links_checked_and_followed = set()


def report_errors(url):
    # check all links
    reset_inits()
    check_all_links_and_follow(url)

    # report errors
    for link in links_checked.values():
        status = link.get('response_status')
        if status != 200:
            print(status, link['url'])


if __name__ == '__main__':
    # read CLI args
    parser = argparse.ArgumentParser(description='Link checker')
    parser.add_argument(
        '-r', '--root-url', help='Root URL', required=True)
    args = parser.parse_args()

    report_errors(args.root_url)
