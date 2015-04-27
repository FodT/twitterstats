import os.path
import unittest
from mock import MagicMock
import datetime
import json
from httmock import all_requests, HTTMock
import sys
import twitter


@all_requests
def api_mocks(url, request):
    max_id = 'max_id={0}'.format(sys.maxint - 1)
    path = os.path.normpath('test/fixtures/rate_limit.json')
    if 'oauth2/token' in url.path:
        path = os.path.normpath('test/fixtures/bearer_token.json')
    elif 'cursor=-1' in url.query:
        path = os.path.normpath('test/fixtures/ids-1.json')
    elif 'cursor=1234' in url.query:
        path = os.path.normpath('test/fixtures/ids-2.json')
    elif 'users/lookup' in url.path:
        path = os.path.normpath('test/fixtures/lookup.json')
    elif '/user_timeline' in url.path and \
            max_id in url.query:
        path = os.path.normpath('test/fixtures/tweets.json')
    elif '/user_timeline' in url.path:
        path = os.path.normpath('test/fixtures/tweet_apr_18_2015.json')
    with open(path, "r") as resource:
        return {'status_code': 200,
                'content': resource.read(),
                'headers': {'x-rate-limit-remaining': 100}}


class TestTwitter(unittest.TestCase):
    def setUp(self):
        self.mock_tdb = MagicMock()
        twitter.credentials_path = os.path.expanduser(
            'test/fixtures/test_credentials')
        with HTTMock(api_mocks):
            self.t = twitter.Twitter(self.mock_tdb)

    def tearDown(self):
        self.t = None
        self.widget = None

    def testIsInitialised(self):
        self.assertEqual(self.t.bearer_token, "THIS_IS_A_BEARER_TOKEN")

    def testGetIds(self):
        with HTTMock(api_mocks):
            ids = self.t.get_followed_ids('user')
            self.assertEqual(len(ids), 30)

    def testGetTweets(self):
        with HTTMock(api_mocks):
            tweets = self.t.get_tweets_by(1)
            self.assertEqual(len(tweets), 200)

    def testSaveUnknownUsers(self):
        with open('test/fixtures/lookup.json') as f:
            unknown_users = [(user['id'], user['screen_name'])
                             for user in json.load(f)]
            unknown_ids = [user[0] for user in unknown_users]
        self.mock_tdb.get_unknown_user_ids = MagicMock(
            return_value=unknown_ids)
        self.mock_tdb.add_user = MagicMock()
        with HTTMock(api_mocks):
            self.t.save_unknown_users(unknown_ids)

        self.assertEqual(self.mock_tdb.add_user.call_count, 3)

    def testGetTweetsUntil(self):
        self.mock_tdb.get_tweets_by = MagicMock(return_value=[])
        with open('test/fixtures/tweets_apr_23_2015.json') as f:
            expected = json.load(f)

        with HTTMock(api_mocks):
            target_date = datetime.datetime(2015, 4, 23)
            tweets = self.t.get_tweets_until(1, target_date)
            self.assertEqual(len(tweets), len(expected))
