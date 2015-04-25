import os.path
import unittest
from httmock import all_requests, HTTMock
import twitter


@all_requests
def api_mocks(url, request):
    path = os.path.normpath('test/fixtures/rate_limit.json')
    if 'oauth2/token' in url.path:
        path = os.path.normpath('test/fixtures/bearer_token.json')
    elif 'cursor=-1' in url.query:
        path = os.path.normpath('test/fixtures/ids-1.json')
    elif 'cursor=1234' in url.query:
        path = os.path.normpath('test/fixtures/ids-2.json')
    with open(path, "r") as resource:
        return {'status_code': 200,
                'content': resource.read()}


class TestTwitter(unittest.TestCase):
    def setUp(self):
        twitter.credentials_path = os.path.expanduser('test/fixtures/test_credentials')
        with HTTMock(api_mocks):
            self.t = twitter.Twitter()

    def tearDown(self):
        self.t = None
        self.widget = None

    def testIsInitialised(self):
        self.assertEqual(self.t.bearer_token, "THIS_IS_A_BEARER_TOKEN")

    def testGetIds(self):
        with HTTMock(api_mocks):
            ids = self.t.get_followed_ids('user')
            self.assertEqual(len(ids), 30)
