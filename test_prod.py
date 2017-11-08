from os import getenv
import json
from base64 import b64encode
import unittest
import requests


class TestLocalAPI(unittest.TestCase):

    def setUp(self):
        self.url = 'https://api.404sentry.com'
        self.credentials = (getenv('TEST_USER'), getenv('TEST_PASSWORD'))
        self.owner_id = 'google-oauth2|105039217801705600811'

    def test_historical_results_response_200(self):
        r = requests.get(
            self.url + '/results/historical',
            data=dict(
                owner_id=self.owner_id,
                url='eightportions.com',
            ),
            auth = self.credentials
        )
        self.assertEqual(r.status_code, 200)

    def test_missing_sources(self):
        for offset in range(0, 2000, 100):
            r = requests.get(
                self.url + '/results/historical',
                data=dict(
                    owner_id=self.owner_id,
                    url='blog.etsy.com',
                    offset=offset,
                    limit=100,
                    filter_exceptions=False
                ),
                auth = self.credentials
            )
            self.assertEqual(r.status_code, 200)
            response = r.json()
            results = response['results']
            sources = response['sources']
            for result in results:
                self.assertIn(result['url'], sources)


if __name__ == '__main__':
    unittest.main()

