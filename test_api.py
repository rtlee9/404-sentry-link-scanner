from app.api import *
from app.models import LinkCheck

class TestAssessSeverity(object):
    def test_assess_severity_404(self):
        link_check = LinkCheck.query.filter(LinkCheck.response == 404).first()
        assert assess_severity(link_check) == 3

    def test_assess_severity_403(self):
        link_check = LinkCheck.query.filter(LinkCheck.response == 403).first()
        assert assess_severity(link_check) == 2

    def test_assess_severity_connectionerror(self):
        link_check = LinkCheck.query.filter(LinkCheck.exception == 'ConnectionError').first()
        assert assess_severity(link_check) == 3

    def test_assess_severity_sslerror(self):
        link_check = LinkCheck.query.filter(LinkCheck.exception == 'SSLError').first()
        assert assess_severity(link_check) == 2

    # LinkedIn respons with non-standard 999 status code
    def test_assess_severity_999(self):
        link_check = LinkCheck.query.filter(LinkCheck.response == 999).first()
        assert assess_severity(link_check) == 1

    def test_assess_javascript_void0(self):
        link_check = LinkCheck.query.filter(LinkCheck.url == 'javascript:void(0)').first()
        assert assess_severity(link_check) == 0
