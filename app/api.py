from flask import request, g
from flask_restful import Api, Resource, reqparse
from flask_httpauth import HTTPBasicAuth
from requests import get
from .models import User
from . import app, scheduler
from .link_check import LinkChecker, scheduled_scan

# auth setup
auth = HTTPBasicAuth()
@auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if not user or not user.verify_password(password):
        return False
    g.user = user
    return True


class Resource(Resource):
    """Adds decorates for all classes inheriting from resource"""
    method_decorators = [auth.login_required]

class LinkScan(Resource):
    def get(self):
        """Scan a website for 404 errors and get a report"""
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, help='URL to check')
        args = parser.parse_args()
        checker = LinkChecker(args.url)
        checker.check_all_links_and_follow()
        return checker.report_errors(lambda status: status == 404)

class LinkScanJob(Resource):
    def post(self):
        """Post a recurring scan job"""
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, help='URL to check')
        args = parser.parse_args()
        cron_params = request.get_json()
        scheduled_scan(args.url, g.user.username, cron_params)

    def get(self):
        """Get information about a recurring scan job"""
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, help='URL to check')
        args = parser.parse_args()
        job = scheduler.get_job('{};{}'.format(username, args.url)
        return(str(job))

api = Api(app)
api.add_resource(LinkScan, "/link-scan")
api.add_resource(LinkScanJob, "/link-scan/schedule")
