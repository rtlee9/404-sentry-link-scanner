from flask import request, g
from flask.json import jsonify
from flask_restful import Api, Resource, reqparse
from flask_httpauth import HTTPBasicAuth
from requests import get
from apscheduler.jobstores.base import ConflictingIdError
from sqlalchemy.exc import IntegrityError
from .models import User, ScanJob, LinkCheck, ScheduledJob, PermissionedURL, Owner, Link
from . import app, scheduler, db
from .link_check import LinkChecker, scheduled_scan, async_scan, standardize_url

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
        Optionally, specify a root URL and/or owner to filter results
        """
        parser = reqparse.RequestParser()
        parser.add_argument('url', required=True, type=str, help='URL to check')
        parser.add_argument('owner_id', type=str, help='Scan job owner ID')
        args = parser.parse_args()
        if (not args.owner_id) or (not g.user.admin):
            owner_id = g.user.username
        else:
            owner_id = args.owner_id
        owner = Owner.query.filter(Owner.user == g.user).filter(Owner.email == owner_id).first()
        last_job_id = db.session.query(db.func.max(ScanJob.id)).\
            filter(ScanJob.user == g.user).\
            filter(ScanJob.owner == owner)
        if args.url:
            last_job_id = last_job_id.filter(ScanJob.root_url == standardize_url(args.url))
        try:
            last_job = ScanJob.query.filter(ScanJob.id == last_job_id.scalar()).all()[-1]
        except IndexError:
            response = jsonify(message='Job not found')
            response.status_code = 404
            return response
        last_job_results = LinkCheck.query.filter(LinkCheck.job == last_job)

        # get sources
        link_sources = Link.query.\
            filter(Link.url.in_(last_job_results.with_entities(LinkCheck.url))).\
            filter(Link.job == last_job).\
            with_entities(Link.url, Link.source_url).all()

        # format sources > error mapping
        source_report = {}
        for link_source in link_sources:
            source_url = link_source.source_url
            url = link_source.url
            source_report[url] = source_report.get(url, []) + [source_url]

        return jsonify(
            job_status=last_job.status,
            results=[result.to_json() for result in last_job_results.all()],
            sources=source_report,
        )


class HistoricalJobs(Resource):
    def get(self):
        """List all historical jobs for a given user.
        Optionally, specify a root URL and/or owner to filter results
        """
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, help='URL to check')
        parser.add_argument('owner_id', type=str, help='Scan job owner')
        args = parser.parse_args()
        if (not args.owner_id) or (not g.user.admin):
            owner_id = g.user.username
        else:
            owner_id = args.owner_id
        owner = Owner.query.filter(Owner.user == g.user).filter(Owner.email == owner_id).first()
        jobs = ScanJob.query.\
            filter(ScanJob.user == g.user).\
            filter(ScanJob.owner == owner)
        if args.url:
            jobs = jobs.filter(ScanJob.root_url == standardize_url(args.url))
        return jsonify([job.to_json() for job in jobs])


class LinkScan(Resource):
    def post(self):
        """Scan a website for 404 errors"""
        parser = reqparse.RequestParser()
        parser.add_argument('url', required=True, type=str, help='URL to check')
        parser.add_argument('owner_id', type=str, help='Scan job owner')
        args = parser.parse_args()
        if (not args.owner_id) or (not g.user.admin):
            owner_id = g.user.username
        else:
            owner_id = args.owner_id
        owner = Owner.query.filter(Owner.user == g.user).filter(Owner.email == owner_id).first()
        # confirm url is permissioned for owner-user
        permissioned = PermissionedURL.query.\
            filter(PermissionedURL.root_url == standardize_url(args.url)).\
            filter(PermissionedURL.owner == owner).\
            filter(PermissionedURL.user == g.user).count()
        if permissioned == 0:
            response = jsonify(
                message='User-owner is not permissioned for this website')
            response.status_code = 403
            return response
        job, _ = async_scan(args.url, g.user, owner)
        return jsonify(job.to_json())

class LinkScanJob(Resource):
    def post(self):
        """Post a recurring scan job"""
        parser = reqparse.RequestParser()
        parser.add_argument('url', required=True, type=str, help='URL to check')
        parser.add_argument('owner_id', type=str, help='Scan job owner')
        args = parser.parse_args()
        if (not args.owner_id) or (not g.user.admin):
            owner_id = g.user.username
        else:
            owner_id = args.owner_id
        owner = Owner.query.filter(Owner.user == g.user).filter(Owner.email == owner_id).first()
        cron_params = request.get_json()
        # confirm url is permissioned for owner-user
        permissioned = PermissionedURL.query.\
            filter(PermissionedURL.root_url == (args.url)).\
            filter(PermissionedURL.owner == owner).\
            filter(PermissionedURL.user == g.user).count()
        if permissioned == 0:
            response = jsonify(
                message='User-owner is not permissioned for this website')
            response.status_code = 403
            return response
        try:
            job = scheduled_scan(args.url, g.user, cron_params, owner)
            return jsonify(job_id=job.id)
        except ConflictingIdError:
            response = jsonify(message='This user already has a scheduled job for the root URL provided.')
            response.status_code = 403
            return response

    def get(self):
        """List scheduled jobs for a given user.
        Optionally, specify a root URL and/or owner to filter results
        """
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, help='URL to check')
        parser.add_argument('owner_id', type=str, help='Scan job owner')
        args = parser.parse_args()
        if (not args.owner_id) or (not g.user.admin):
            owner_id = g.user.username
        else:
            owner_id = args.owner_id
        owner = Owner.query.filter(Owner.user == g.user).filter(Owner.email == owner_id).first()
        jobs = ScheduledJob.query.\
            filter(ScheduledJob.user == g.user).\
            filter(ScheduledJob.owner == owner)
        if args.url:
            jobs = jobs.filter(ScheduledJob.root_url == standardize_url(args.url))
        scheduled_jobs = filter(
            lambda x: x is not None,
            [scheduler.get_job(str(job.id)) for job in jobs])
        return jsonify([
            dict(
                next_run_time=job.next_run_time,
                trigger=str(job.trigger),
                cron_pattern=str(job.trigger)[:-1].split('[')[1],
            )
            for job in scheduled_jobs
        ])


class UrlPermissions(Resource):
    def post(self):
        """Add permissioned URL for a given user (requires admin rights)"""
        parser = reqparse.RequestParser()
        parser.add_argument('url', required=True, type=str, help='URL to check')
        parser.add_argument('owner_id', type=str, help='Scan job owner')
        parser.add_argument(
            'stripe_subscription_id', type=str, help='Stripe subscription ID')
        args = parser.parse_args()
        if (not args.owner_id) or (not g.user.admin):
            owner_id = g.user.username
        else:
            owner_id = args.owner_id
        if not g.user.admin:
            response = jsonify(message='This method requires admin rights.')
            response.status_code = 403
            return response
        owner = Owner.query.filter(Owner.user == g.user).filter(Owner.email == owner_id).first()
        try:
            permissioned_url = PermissionedURL(
                root_url=standardize_url(args.url),
                user=g.user,
                owner=owner,
                stripe_subscription_id=args.stripe_subscription_id,
            )
            db.session.add(permissioned_url)
            db.session.commit()
            return jsonify(permissioned_url.to_json())
        except IntegrityError:
            db.session.rollback()
            permissioned_url = PermissionedURL.query.\
                filter(PermissionedURL.root_url == standardize_url(args.url)).\
                filter(PermissionedURL.user == g.user).\
                filter(PermissionedURL.owner == owner).first()
            response = jsonify(
                message='URl already permissioned',
                permissioned_url=permissioned_url.to_json(),
            )
            response.status_code = 403
            return response

    def patch(self):
        """Update permissioned URL for a given user
        with provided URL paramters by job ID(requires admin rights)"""
        parser = reqparse.RequestParser()
        parser.add_argument('id', required=True, type=str, help='Permissioned URL ID')
        parser.add_argument('url', required=True, type=str, help='URL to check')
        parser.add_argument('owner_id', type=str, help='Scan job owner')
        parser.add_argument(
            'stripe_subscription_id', required=True, type=str, help='Stripe subscription ID')
        args = parser.parse_args()
        if (not args.owner_id) or (not g.user.admin):
            owner_id = g.user.username
        else:
            owner_id = args.owner_id
        if not g.user.admin:
            response = jsonify(message='This method requires admin rights.')
            response.status_code = 403
            return response
        owner = Owner.query.filter(Owner.user == g.user).filter(Owner.email == owner_id).first()

        permissioned_url = PermissionedURL.query.filter(PermissionedURL.id == args.id).first()
        permissioned_url.stripe_subscription_id = args.stripe_subscription_id
        db.session.commit()
        return jsonify(permissioned_url.to_json())

    def delete(self):
        """Delete permissioned URL for a given user (requires admin rights)"""
        parser = reqparse.RequestParser()
        parser.add_argument('url', required=True, type=str, help='URL to check')
        parser.add_argument('owner_id', type=str, help='Scan job owner')
        args = parser.parse_args()
        if (not args.owner_id) or (not g.user.admin):
            owner_id = g.user.username
        else:
            owner_id = args.owner_id
        if not g.user.admin:
            response = jsonify(message='This method requires admin rights.')
            response.status_code = 403
            return response
        owner = Owner.query.filter(Owner.user == g.user).filter(Owner.email == owner_id).first()
        depermissioned_urls = PermissionedURL.query.\
            filter(PermissionedURL.root_url == standardize_url(args.url)).\
            filter(PermissionedURL.user == g.user).\
            filter(PermissionedURL.owner == owner).all()
        if len(depermissioned_urls) == 0:
            response = jsonify(
                message='Resource not found')
            response.status_code = 404
            return response
        depermissioned_url_details = [url.to_json() for url in depermissioned_urls]
        for depermissioned_url in depermissioned_urls:
            db.session.delete(depermissioned_url)
        db.session.commit()
        return jsonify(depermissioned_url_details)

    def get(self):
        """Add permissioned URL for a given user (requires admin rights)"""
        parser = reqparse.RequestParser()
        parser.add_argument('owner_id', type=str, help='Scan job owner')
        args = parser.parse_args()
        if (not args.owner_id) or (not g.user.admin):
            owner_id = g.user.username
        else:
            owner_id = args.owner_id
        if not g.user.admin:
            response = jsonify(message='This method requires admin rights.')
            response.status_code = 403
            return response
        owner = Owner.query.filter(Owner.user == g.user).filter(Owner.email == owner_id).first()
        permissioned_urls = PermissionedURL.query.\
            filter(PermissionedURL.owner == owner).\
            filter(PermissionedURL.user == g.user)
        return jsonify([
            permissioned_url.root_url
            for permissioned_url in permissioned_urls])

class Owners(Resource):
    def post(self):
        """Add owner resource (requires admin rights)"""
        parser = reqparse.RequestParser()
        parser.add_argument('stripe_token', type=str, help='Stripe token')
        parser.add_argument('stripe_email', type=str, help='Email from Stripe checkout')
        parser.add_argument('stripe_customer_id', type=str, help='Stripe customer ID')
        parser.add_argument('owner_id', type=str, help='Scan job owner')
        args = parser.parse_args()
        if (not args.owner_id) or (not g.user.admin):
            owner_id = g.user.username
        else:
            owner_id = args.owner_id
        if not g.user.admin:
            response = jsonify(message='This method requires admin rights.')
            response.status_code = 403
            return response
        try:
            owner = Owner(
                email=owner_id,
                user=g.user,
                stripe_token=args.stripe_token,
                stripe_email=args.stripe_email,
                stripe_customer_id=args.stripe_customer_id,
            )
            db.session.add(owner)
            db.session.commit()
            return jsonify(owner.to_json())
        except IntegrityError:
            db.session.rollback()
            owner = Owner.query.\
                filter(Owner.email == owner_id).\
                filter(Owner.user == g.user).first()
            response = jsonify(message='Owner already exists', owner=owner.to_json())
            response.status_code = 403
            return response

    def patch(self):
        """Patch owner by owner ID (requires admin rights)"""
        parser = reqparse.RequestParser()
        parser.add_argument('stripe_token', type=str, help='Stripe token')
        parser.add_argument('stripe_email', type=str, help='Email from Stripe checkout')
        parser.add_argument('stripe_customer_id', type=str, help='Stripe customer ID')
        parser.add_argument('owner_id', type=str, help='Scan job owner')
        parser.add_argument('id', required=True, type=int, help='API owner ID')
        args = parser.parse_args()
        if (not args.owner_id) or (not g.user.admin):
            owner_id = g.user.username
        else:
            owner_id = args.owner_id
        if not g.user.admin:
            response = jsonify(message='This method requires admin rights.')
            response.status_code = 403
            return response
        try:
            owner = Owner.query.filter(Owner.id == args.id).first()
            owner.email=owner_id
            owner.user=g.user
            owner.stripe_token=args.stripe_token
            owner.stripe_email=args.stripe_email
            owner.stripe_customer_id=args.stripe_customer_id
            db.session.commit()
            return jsonify(owner.to_json())
        except AttributeError:
            db.session.rollback()
            response = jsonify(message='Owner does not exist')
            response.status_code = 404
            return response

    def get(self):
        """Get owner resource (requires admin rights)"""
        parser = reqparse.RequestParser()
        parser.add_argument('owner_id', required=True, type=str)
        args = parser.parse_args()
        if (not args.owner_id) or (not g.user.admin):
            owner_id = g.user.username
        else:
            owner_id = args.owner_id
        if not g.user.admin:
            response = jsonify(message='This method requires admin rights.')
            response.status_code = 403
            return response
        try:
            owner = Owner.query.\
                filter(Owner.email == owner_id).\
                filter(Owner.user == g.user).first()
            return jsonify(owner.to_json())
        except AttributeError:
            response = jsonify(message='Owner does not exist')
            response.status_code = 404
            return response

api = Api(app)
api.add_resource(LinkScan, "/link-scan")
api.add_resource(HistoricalJobs, "/jobs/historical")
api.add_resource(HistoricalResults, "/results/historical")
api.add_resource(LinkScanJob, "/link-scan/schedule")
api.add_resource(UrlPermissions, "/permissions")
api.add_resource(Owners, "/owners")
