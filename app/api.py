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
    method_decorators = [auth.login_required]

class Link(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, help='URL to check')
        args = parser.parse_args()
        checker = LinkChecker(args.url)
        checker.check_all_links_and_follow()
        return checker.report_errors(lambda status: status == 404)

class ScanJob(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, help='URL to check')
        args = parser.parse_args()
        cron_params = request.get_json()
        scheduled_scan(args.url, g.user.username, cron_params)

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, help='URL to check')
        args = parser.parse_args()
        job = scheduler.get_job('{};{}'.format(username, args.url)
        return(str(job))

api = Api(app)
api.add_resource(Link, "/link")
api.add_resource(ScanJob, "/link/schedule")
