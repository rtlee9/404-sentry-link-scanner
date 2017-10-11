import time
from app.link_check import *
from app.models import User


def test_performance_comparatory():
    user = User.query.first()
    t0 = time.time()
    test_checker = LinkChecker('https://comparatory.io', user)
    test_checker.check_all_links_and_follow()
    print('{:.1f} seconds elapsed'.format(time.time() - t0))
    assert(time.time() - t0 < 30)


def test_performance_eightportions():
    user = User.query.first()
    t0 = time.time()
    test_checker = LinkChecker('https://eightportions.com', user)
    test_checker.check_all_links_and_follow()
    print('{:.1f} seconds elapsed'.format(time.time() - t0))
    assert(time.time() - t0 < 150)
