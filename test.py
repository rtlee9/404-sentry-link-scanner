from app.link_check import *
from app.models import User

def test_get_all_links_len_8P():
    assert len(get_all_links('http://eightportions.com')) > 15


def test_get_base_url():
    assert get_base_url('https://eightportions.com') == 'eightportions.com'
    assert get_base_url('http://eightportions.com') == 'eightportions.com'
    assert get_base_url('http://eightportions.com/') == 'eightportions.com'
    assert get_base_url('https://eightp//ortions.com') == 'eightp//ortions.com'


def test_get_hostname():
    assert get_hostname('https://eightportions.com') == 'https://eightportions.com'
    assert get_hostname('http://eightportions.com') == 'http://eightportions.com'
    assert get_hostname('http://eightportions.com/') == 'http://eightportions.com'
    assert get_hostname('http://eightportions.com/asdf') == 'http://eightportions.com'
    assert get_hostname('http://eightportions.com/asdf/dsf1') == 'http://eightportions.com'


def test_points_to_self():
    assert points_to_self('/', 'asdf')
    assert points_to_self('https://eightportions.com', 'https://eightportions.com')
    assert points_to_self('http://eightportions.com', 'https://eightportions.com')
    assert points_to_self('http://eightpor//tions.com', 'https://eightpor//tions.com')
    assert ~points_to_self('http://eightport//ions.com', 'https://eightpor//tions.com')


def test_internal_link():
    assert is_internal_link('/', 'https://eightportions.com')
    assert is_internal_link('/', 'asdfa')
    assert is_internal_link('https://eightportions.com', 'https://eightportions.com')
    assert ~is_internal_link('https://eightportions.com', 'https://eightporasdf.com')


def test_prepend_if_relative():
    assert prepend_if_relative('/', 'https://eightportions.com') == 'https://eightportions.com/'
    assert prepend_if_relative('/page', 'https://eightportions.com') == 'https://eightportions.com/page'
    assert prepend_if_relative('/page', 'http://eightportions.com') == 'http://eightportions.com/page'
    assert prepend_if_relative('/page1/subpage1', 'http://eightportions.com') == 'http://eightportions.com/page1/subpage1'
    assert prepend_if_relative('http://eightportions.com', 'http://eightportions.com') == 'http://eightportions.com'


def test_is_flat_file():
    assert not is_flat_file('http://eightportions.com')
    assert not is_flat_file('https://eightportions.com')
    assert not is_flat_file('https://eightportions.zip')
    assert is_flat_file('https://eightportions/test.zip')
    assert is_flat_file('https://eightportions/test.json')
    assert not is_flat_file('https://www.tensorflow.org/versions/r0.11/tutorials/wide_and_deep/index.html#tensorflow-wide-deep-learning-tutorial')
    assert not is_flat_file('http://www.informit.com/articles/article.aspx?p=2314818')


def test_standardize_url():
    assert standardize_url('https://eightportions.com ') == 'https://eightportions.com'
    assert standardize_url('https://eightportions.com') == 'https://eightportions.com'
    assert standardize_url('https://eightportions.com/ ') == 'https://eightportions.com'
    assert standardize_url('https://eightportions.com/') == 'https://eightportions.com'
    assert standardize_url('http://eightportions.com') == 'http://eightportions.com'
    assert standardize_url('http://eightportions.com ') == 'http://eightportions.com'
    assert standardize_url('eightportions.com ') == 'http://eightportions.com'
    assert standardize_url('/') == '/'
    assert standardize_url('/asdf') == '/asdf'
    assert standardize_url('#') == '#'
    assert standardize_url('#asdf') == '#asdf'


def test_links_checked_and_followed():
    user = User.query.first()
    test_checker = LinkChecker('https://eightportions.com/img/Taxi_pick_by_drop.gif', user)
    test_checker.check_all_links_and_follow()
    assert test_checker.links_checked == []
    assert test_checker.check_link('https://storage.googleapis.com/recipe-box/recipes_raw.zip').note == 'Flat file not checked'
