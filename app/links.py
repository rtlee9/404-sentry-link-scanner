from flask_restful import Resource, reqparse
from requests import get
from link_check import LinkChecker


class Link(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, help='URL to check')
        args = parser.parse_args()
        checker = LinkChecker(args.url)
        checker.check_all_links_and_follow()
        return checker.report_errors(lambda status: status == 404)
