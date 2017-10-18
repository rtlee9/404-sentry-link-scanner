from app.link_check import *
from app.models import Owner


class TestLinkCheck(object):
    def setup(self):
        self.owner = Owner.query.first()
        self.test_checker = LinkChecker(
            'https://stripe.com/blog',
            self.owner.user,
            self.owner
        )

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

    def test_links_checked_and_followed(self):
        test_checker = LinkChecker(
            'https://eightportions.com/datasets',
            self.owner.user,
            self.owner)
        test_checker.check_all_links_and_follow()
        assert len(test_checker.links_checked_and_followed) > 2

    def test_long_response_siafoo(self):
        r = self.test_checker.check_link('http://www.siafoo.net/article/52')
        assert r.response == 200

    def test_long_response_djaverages(self):
        r = self.test_checker.check_link('http://www.djaverages.com/?go=industrial-calculation')
        assert r.response == 200
