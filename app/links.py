from flask_restful import Resource, reqparse
from requests import get
from .link_check import repeating_scan_job, scan_job
from . import huey


class Link(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, help='URL to check')
        parser.add_argument('delay', type=int, help='delay for job', default=0)
        args = parser.parse_args()
        scanner = scan_job.schedule(args=(args.url,), delay=0)
        scanner(blocking=True)
        repeating_scan_job(args.url, delay=args.delay)
