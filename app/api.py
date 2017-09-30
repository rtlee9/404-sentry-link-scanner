from flask import request, g
from flask.json import jsonify
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
    def post(self):
        """Scan a website for 404 errors"""
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, help='URL to check')
        parser.add_argument('owner', type=str, help='Scan job owner')
        args = parser.parse_args()
        owner = args.owner if g.user.admin else None
        checker = LinkChecker(args.url, owner)
        checker.check_all_links_and_follow()
        return jsonify(checker.report_errors(lambda status: status == 404))

class LinkScanJob(Resource):
    def post(self):
        """Post a recurring scan job"""
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, help='URL to check')
        parser.add_argument('owner', type=str, help='Scan job owner')
        args = parser.parse_args()
        owner = args.owner if g.user.admin else None
        cron_params = request.get_json()
        job = scheduled_scan(args.url, g.user.username, cron_params, owner)
        return jsonify(job_id=job.id)

    def get(self):
        """Get information about a recurring scan job"""
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, help='URL to check')
        parser.add_argument('owner', type=str, help='Scan job owner')
        args = parser.parse_args()
        owner = args.owner if g.user.admin else None
        job = scheduler.get_job('{};{};{}'.format(g.user.username, owner, args.url))
        return jsonify(job_id=job.id)

api = Api(app)
api.add_resource(LinkScan, "/link-scan")
api.add_resource(LinkScanJob, "/link-scan/schedule")
