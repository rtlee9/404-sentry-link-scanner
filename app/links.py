from flask_restful import Resource, reqparse
from flask import request
from requests import get
from .link_check import LinkChecker, scheduled_scan
from . import scheduler


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
        scheduled_scan(args.url, cron_params)

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, help='URL to check')
        args = parser.parse_args()
        job = scheduler.get_job(args.url)
        return(str(job))
