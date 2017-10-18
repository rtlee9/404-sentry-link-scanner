from app.link_check import *


def test_get_all_links_len_8P():
    assert len(get_all_links('http://eightportions.com')) > 15


def test_get_base_url():
    assert get_base_url('https://eightportions.com') == 'eightportions.com'
    assert get_base_url('http://eightportions.com') == 'eightportions.com'
    assert get_base_url('http://eightportions.com/') == 'eightportions.com'
    assert get_base_url('https://eightp//ortions.com') == 'eightp//ortions.com'


def test_get_base_url_no_protocol():
    assert get_base_url('eightportions.com') == 'eightportions.com'


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
    assert not points_to_self('http://eightport//ions.com', 'https://eightpor//tions.com')


def test_internal_link():
    assert is_internal_link('/', 'https://eightportions.com')
    assert is_internal_link('/', 'asdfa')
    assert is_internal_link('https://eightportions.com', 'https://eightportions.com')
    assert not is_internal_link('https://eightportions.com', 'https://eightporasdf.com')


def test_internal_link_relative():
    assert is_internal_link('../open-source/bletchley/', 'http://tech.labs.oliverwyman.com/blog/2017/09/06/gasconade-making-blog-posts-for-twitter-users/')


def test_standardize_url_slash_anchor():
    assert standardize_url('http://tech.labs.oliverwyman.com/blog/2017/06/19/android-widget-for-dragon-go-server/#respond') == 'http://tech.labs.oliverwyman.com/blog/2017/06/19/android-widget-for-dragon-go-server'


def test_is_internal_link_double_slash():
    assert not is_internal_link('//www.pinterest.com/pin/create/button/', 'http://nonnompaleo.com')


def test_standardize_double_slash():
    assert standardize_url('//www.pinterest.com/pin/create/button/') == 'http://www.pinterest.com/pin/create/button'


def test_standardize_url_relative():
    assert standardize_url('../open-source/bletchley') == '../open-source/bletchley'


def test_standardize_url_relative_trailing_slash():
    assert standardize_url('../open-source/bletchley/') == '../open-source/bletchley'


def test_standardize_url_internal_trailing_slash():
    assert standardize_url('/open-source/bletchley/') == '/open-source/bletchley'


def test_internal_link_no_protocol():
    assert is_internal_link('eightportions.com', 'https://eightportions.com')
    assert not is_internal_link('eightportionssdf.com', 'https://eightportions.com')


def test_prepend_if_relative():
    assert prepend_if_relative('/', 'https://eightportions.com') == 'https://eightportions.com/'
    assert prepend_if_relative('/page', 'https://eightportions.com') == 'https://eightportions.com/page'
    assert prepend_if_relative('/page', 'http://eightportions.com') == 'http://eightportions.com/page'
    assert prepend_if_relative('#anchor1', 'http://eightportions.com') == 'http://eightportions.com'
    assert prepend_if_relative('#anchor1', 'http://eightportions.com', keep_anchors=True) == 'http://eightportions.com#anchor1'
    assert prepend_if_relative('/page1/subpage1', 'http://eightportions.com') == 'http://eightportions.com/page1/subpage1'
    assert prepend_if_relative('http://eightportions.com', 'http://eightportions.com') == 'http://eightportions.com'


def test_prepend_if_relative_relative_sibling():
    assert prepend_if_relative('../sibling-section', 'https://eightportions.com/section') == 'https://eightportions.com/sibling-section'


def test_prepend_if_relative_relative_nephew():
    assert prepend_if_relative('../sibling-section/child-section', 'https://eightportions.com/section') == 'https://eightportions.com/sibling-section/child-section'


def test_is_flat_file():
    assert not is_flat_file('http://eightportions.com')
    assert not is_flat_file('https://eightportions.com')
    assert not is_flat_file('https://eightportions.zip')
    assert is_flat_file('https://eightportions/test.zip')
    assert is_flat_file('https://eightportions/test.json')
    assert not is_flat_file('https://www.tensorflow.org/versions/r0.11/tutorials/wide_and_deep/index.html#tensorflow-wide-deep-learning-tutorial')
    assert not is_flat_file('http://www.informit.com/articles/article.aspx?p=2314818')


def test_remove_trailing_slash():
    assert remove_trailing_slash('www.example.com/') == 'www.example.com'
    assert remove_trailing_slash('http://example.com/') == 'http://example.com'
    assert remove_trailing_slash('http://example.com') == 'http://example.com'
    assert remove_trailing_slash('/') == '/'


def test_standardize_url():
    assert standardize_url('https://eightportions.com ') == 'http://eightportions.com'
    assert standardize_url('https://eightportions.com') == 'http://eightportions.com'
    assert standardize_url('https://eightportions.com/ ') == 'http://eightportions.com'
    assert standardize_url('https://eightportions.com/') == 'http://eightportions.com'
    assert standardize_url('http://eightportions.com') == 'http://eightportions.com'
    assert standardize_url('http://eightportions.com ') == 'http://eightportions.com'
    assert standardize_url('eightportions.com ') == 'http://eightportions.com'
    assert standardize_url('/') == '/'
    assert standardize_url('/asdf') == '/asdf'
    assert standardize_url('/section/#anchor') == '/section/#anchor'
    assert standardize_url('#') == '#'
    assert standardize_url('#asdf') == '#asdf'
    assert standardize_url('//www.pinterest.com/pin/create/button/') == 'http://www.pinterest.com/pin/create/button'

def test_ensure_protocol():
    assert ensure_protocol('https://github.com/daattali') == 'https://github.com/daattali'
    assert ensure_protocol('http://github.com/daattali') == 'http://github.com/daattali'
    assert ensure_protocol('github.com/daattali') == 'http://github.com/daattali'
    assert ensure_protocol('github.com/daattali', 'https') == 'https://github.com/daattali'


def test_ensure_protocol_ftp():
    assert ensure_protocol('ftp://cran.r-project.org/pub/R/web/packages/data.table/vignettes/datatable-reshape.html') == 'ftp://cran.r-project.org/pub/R/web/packages/data.table/vignettes/datatable-reshape.html'


def test_ensure_protocol_double_slash():
    assert ensure_protocol('//www.pinterest.com/pin/create/button/') == 'http://www.pinterest.com/pin/create/button/'


def test_standardize_url_ftp():
    assert standardize_url('ftp://cran.r-project.org/pub/R/web/packages/data.table/vignettes/datatable-reshape.html') == 'ftp://cran.r-project.org/pub/R/web/packages/data.table/vignettes/datatable-reshape.html'
