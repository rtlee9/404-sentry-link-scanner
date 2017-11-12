from os import path
from app.link_check import *
from app.models import Owner
from unittest.mock import patch


class TestLinkCheck(object):
    def setup(self):
        self.owner = Owner.query.first()
        self.test_checker = LinkChecker(
            'https://stripe.com/blog',
            self.owner.user,
            self.owner
        )
        self.sample_html = """
        <HTML>
        <HEAD>
        <TITLE>Your Title Here</TITLE>
        </HEAD>
        <BODY BGCOLOR="FFFFFF">
        <CENTER><IMG SRC="clouds.jpg" ALIGN="BOTTOM"> </CENTER>
        <HR>
        <a href="http://somegreatsite.com">Link Name</a>
        <a href="https://blog.dummy.com/internal-link1">Link Name</a>
        <a href="https://blog.dummy.com/internal-link2">Link Name</a>
        is a link to another nifty site
        <H1>This is a Header</H1>
        <H2>This is a Medium Header</H2>
        Send me mail at <a href="mailto:support@yourcompany.com">
        support@yourcompany.com</a>.
        <P> This is a new paragraph!
        <P> <B>This is a new paragraph!</B>
        <BR> <B><I>This is a new sentence without a paragraph break, in bold italics.</I></B>
        <HR>
        </BODY>
        </HTML>
        """

    def test_flat_follow(self):
        test_checker = LinkChecker(
            'https://eightportions.com/img/Taxi_pick_by_drop.gif',
            self.owner.user,
            self.owner)
        test_checker.check_all_links_and_follow()
        assert test_checker

    def test_zip_file(self):
        r = self.test_checker.check_link('https://storage.googleapis.com/recipe-box/recipes_raw.zip')
        assert r.response == 200

    def test_link_stripe(self):
        assert self.test_checker.check_link('https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2').response == 200

    def test_ssl_err_catch(self):
        r = self.test_checker.check_link('http://www.sysads.co.uk/2014/06/install-r-base-3-1-0-ubuntu-14-04/')
        assert r.response is None
        assert r.exception == "SSLError"

    def test_invalid_URL(self):
        r = self.test_checker.check_link('http://')
        assert r.response is None
        assert r.exception == "InvalidURL"

    def test_max_retries(self):
        r = self.test_checker.check_link('http://mongolab.com')
        assert r.response is None
        assert r.exception == "ConnectTimeout"

    @patch('app.link_check.requests.get')
    def test_links_checked_and_followed_single_page(self, mock_get):
        mock_get.return_value.status_code = 404
        mock_get.return_value.content = self.sample_html
        test_checker = LinkChecker(
            'https://blog.dummy.com',
            self.owner.user,
            self.owner)
        test_checker.check_all_links_and_follow()
        assert len(test_checker.links_checked_and_followed) == 3

    @patch('app.link_check.requests.get')
    def test_links_checked_and_followed_single_page_no_schema(self, mock_get):
        mock_get.return_value.status_code = 404
        mock_get.return_value.content = self.sample_html
        test_checker = LinkChecker(
            'blog.dummy.com',
            self.owner.user,
            self.owner)
        test_checker.check_all_links_and_follow()
        assert len(test_checker.links_checked_and_followed) == 3

    def test_long_response_siafoo(self):
        r = self.test_checker.check_link('http://www.siafoo.net/article/52')
        assert r.response == 200

    def test_long_response_djaverages(self):
        r = self.test_checker.check_link('http://www.djaverages.com/?go=industrial-calculation')
        assert r.response == 200

    @patch('app.link_check.requests.get')
    def test_stokes(self, mock_get):
        with open(path.join('samples', 'stokes.html'), 'r') as f:
            sample_html = f.read()
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = sample_html
        test_checker = LinkChecker(
            'http://www.stokes4senate.com/forms/shares/new',
            self.owner.user,
            self.owner)
        test_checker.check_all_links_and_follow()
        results = test_checker.get_results(lambda x: True).all()
        links_checked = [result.url for result in results]
        assert set(links_checked) == set([
            'http://www.stokes4senate.com/login',
            'mailto:?body=',
            'http://www.facebook.com/share.php?u=',
            'http://www.stokes4senate.com/forms/shares/new',
        ])

    @patch('app.link_check.requests.get')
    def test_dot_asp_va(self, mock_get):
        with open(path.join('samples', 'va.html'), 'r') as f:
            sample_html = f.read()
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = sample_html
        test_checker = LinkChecker(
            'https://www.va.gov/HEALTHBENEFITS/cost/',
            self.owner.user,
            self.owner)
        test_checker.check_all_links_and_follow()
        results = test_checker.get_results(lambda x: True).all()
        links_checked = [result.url for result in results]
        asp_links = [link for link in links_checked if 'copays.asp' in link]
        assert 'http://copays.asp' not in asp_links

    @patch('app.link_check.requests.get')
    def test_relative_ext_va(self, mock_get):
        with open(path.join('samples', 'va_directory.html'), 'r') as f:
            sample_html = f.read()
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = sample_html
        test_checker = LinkChecker(
            'https://www.va.gov/directory/guide/home.asp',
            self.owner.user,
            self.owner)
        test_checker.check_all_links_and_follow()
        results = test_checker.get_results(lambda x: True).all()
        links_checked = [result.url for result in results]
        assert 'http://./PTSD.asp' not in links_checked
        assert 'http://www.va.gov/directory/guide/PTSD.asp' in links_checked

    @patch('app.link_check.requests.get')
    def test_relative_no_dot_slash(self, mock_get):
        with open(path.join('samples', 'va_ptsd.html'), 'r') as f:
            sample_html = f.read()
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = sample_html
        test_checker = LinkChecker(
            'https://www.va.gov/directory/guide/PTSD.asp',
            self.owner.user,
            self.owner)
        test_checker.check_all_links_and_follow()
        results = test_checker.get_results(lambda x: True).all()
        links_checked = [result.url for result in results]
        assert 'http://state_PTSD.cfm?STATE=VI' not in links_checked
        assert 'http://www.va.gov/directory/guide/state_PTSD.cfm' in links_checked

    @patch('app.link_check.requests.get')
    def test_relative_dot_xml(self, mock_get):
        with open(path.join('samples', 'va_recovery.html'), 'r') as f:
            sample_html = f.read()
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = sample_html
        test_checker = LinkChecker(
            'https://www.va.gov/directory/guide/PTSD.asp',
            self.owner.user,
            self.owner)
        test_checker.check_all_links_and_follow()
        results = test_checker.get_results(lambda x: True).all()
        links_checked = [result.url for result in results]
        assert 'http://Major_Communications.xml' not in links_checked