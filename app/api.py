from flask import request, g
from flask.json import jsonify
from flask_restful import Api, Resource, reqparse
from flask_httpauth import HTTPBasicAuth
from requests import get
from apscheduler.jobstores.base import ConflictingIdError
from .models import User, ScanJob, LinkCheck
from . import app, scheduler, db
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


class HistoricalResults(Resource):
    def get(self):
        """Return the results of a historical job for a given user.
        Optionally, specify a root URL, job ID, and/or owner to filter results
        """
        parser = reqparse.RequestParser()
        parser.add_argument('url', required=True, type=str, help='URL to check')
        parser.add_argument('owner', type=str, help='Scan job owner')
        parser.add_argument('job_id', type=str, help='Job ID')
        args = parser.parse_args()
        owner = args.owner if g.user.admin else None
        if args.job_id:
            job_id = args.job_id
        else:
            last_job_id = db.session.query(db.func.max(ScanJob.id)).filter(ScanJob.user == g.user)
            if owner:
                last_job_id = last_job_id.filter(ScanJob.owner == g.owner)
            if args.url:
                last_job_id = last_job_id.filter(ScanJob.root_url == args.url)
            job_id = last_job_id.scalar()
        last_job_results = LinkCheck.query.filter(LinkCheck.job_id == job_id).all()
        return jsonify([result.to_json() for result in last_job_results])


class HistoricalJobs(Resource):
    def get(self):
        """List all historical jobs for a given user.
        Optionally, specify a root URL and/or owner to filter results
        """
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, help='URL to check')
        parser.add_argument('owner', type=str, help='Scan job owner')
        args = parser.parse_args()
        owner = args.owner if g.user.admin else None
        jobs = ScanJob.query.filter(ScanJob.user == g.user)
        if owner:
            jobs = jobs.filter(ScanJob.owner == owner)
        if args.url:
            jobs = jobs.filter(ScanJob.root_url == args.url)
        return jsonify([job.to_json() for job in jobs])


class LinkScan(Resource):
    def post(self):
        """Scan a website for 404 errors"""
        parser = reqparse.RequestParser()
        parser.add_argument('url', required=True, type=str, help='URL to check')
        parser.add_argument('owner', type=str, help='Scan job owner')
        args = parser.parse_args()
        owner = args.owner if g.user.admin else None
        checker = LinkChecker(args.url, g.user, owner)
        checker.check_all_links_and_follow()
        return jsonify(checker.report_errors(lambda status: status == 404))

class LinkScanJob(Resource):
    def post(self):
        """Post a recurring scan job"""
        parser = reqparse.RequestParser()
        parser.add_argument('url', required=True, type=str, help='URL to check')
        parser.add_argument('owner', type=str, help='Scan job owner')
        args = parser.parse_args()
        owner = args.owner if g.user.admin else None
        cron_params = request.get_json()
        try:
            job = scheduled_scan(args.url, g.user, cron_params, owner)
            return jsonify(job_id=job.id)
        except ConflictingIdError:
            response = jsonify(message='This user already has a scheduled job for the root URL provided.')
            response.status_code = 403
            return response

    def get(self):
        """Get information about a recurring scan job"""
        parser = reqparse.RequestParser()
        parser.add_argument('url', required=True, type=str, help='URL to check')
        parser.add_argument('owner', type=str, help='Scan job owner')
        args = parser.parse_args()
        owner = args.owner if g.user.admin else None
        job = scheduler.get_job('{};{};{}'.format(g.user.username, owner, args.url))
        return jsonify(job_id=job.id)

api = Api(app)
api.add_resource(LinkScan, "/link-scan")
api.add_resource(HistoricalJobs, "/jobs/historical")
api.add_resource(HistoricalResults, "/results/historical")
api.add_resource(LinkScanJob, "/link-scan/schedule")
