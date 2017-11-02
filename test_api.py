from os import getenv
import json
from base64 import b64encode
import unittest
from app import app


BATCH_SIZE = 50
N_RESULTS = 2000


class TestHistoricalresults(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        credentials = (getenv('TEST_USER'), getenv('TEST_PASSWORD'))
        auth = b64encode(bytes("{0}:{1}".format(*credentials), 'utf-8')).decode('ascii')
        self.headers = {'Authorization': 'Basic ' + auth}
        self.owner_id = 'google-oauth2|105039217801705600811'

    def test_response_200(self):
        r = self.app.get(
            '/results/historical',
            query_string=dict(
                owner_id=self.owner_id,
                url='eightportions.com',
                offset=0,
                limit=BATCH_SIZE,
                filter_exceptions=False
            ),
            headers = self.headers
        )
        self.assertEqual(r.status_code, 200)

    def test_limit(self):
        r = self.app.get(
            '/results/historical',
            query_string=dict(
                owner_id=self.owner_id,
                url='eightportions.com',
                offset=0,
                limit=BATCH_SIZE,
                filter_exceptions=False
            ),
            headers = self.headers
        )
        self.assertEqual(r.status_code, 200)
        response = json.loads(r.get_data(as_text=True))
        print(response)
        results = response['results']
        self.assertEqual(len(results), BATCH_SIZE)

    def test_missing_sources(self):
        for offset in range(0, N_RESULTS, BATCH_SIZE):
            r = self.app.get(
                '/results/historical',
                query_string=dict(
                    owner_id=self.owner_id,
                    url='eightportions.com',
                    offset=offset,
                    limit=BATCH_SIZE,
                    filter_exceptions=False
                ),
                headers = self.headers
            )
            self.assertEqual(r.status_code, 200)
            response = json.loads(r.get_data(as_text=True))
            results = response['results']
            sources = response['sources']
            for result in results:
                self.assertIn(result['url'], sources)


if __name__ == '__main__':
    unittest.main()
