import base64
import json
import os
import requests
import urllib
import sys
from datetime import datetime, timedelta
from twitterdb import Tweet, User
import logging

credentials = {
    'key': 'GET_YOUR_OWN',
    'secret': 'GET_YOUR_OWN'}

base_api_url = 'https://api.twitter.com/1.1/'
base_oauth_url = 'https://api.twitter.com/oauth2/'

credentials_path = os.path.expanduser('twitter_credentials')
logger = logging.getLogger('twitter')


class TwitterException(Exception):
    pass


def save_credentials(fn, data):
    with open(fn, 'w') as f:
        json.dump(data, f)


def load_credentials(fn):
    with open(fn) as f:
        result = json.load(f)
    return result


def get_application_only_token(consumer_key, consumer_secret):
    key = urllib.quote_plus(consumer_key)
    secret = urllib.quote_plus(consumer_secret)

    access_token = base64.b64encode(':'.join([key, secret]))

    headers = {'Authorization': 'Basic ' + access_token,
               'Content-Type': 'application/x-www-form-urlencoded;'
                               'charset=UTF-8'}
    payload = 'grant_type=client_credentials'
    r = requests.post(base_oauth_url + 'token', headers=headers, data=payload)
    if r.status_code != 200:
        raise TwitterException('Failed to get authentication token')

    bearer_token = json.loads(r.content)['access_token']
    return bearer_token


def assert_request_success(r, expected_code, error_string):
    if r.status_code != expected_code:
        content = json.loads(r.content)
        errors = content['errors']
        error = content['error'] if not errors else errors[0]
        error_msg = '{0}; HTTP status {1}, twitter code {2}, message: {3}' \
            .format(error_string, r.status_code,
                    error['code'], error['message'])
        raise TwitterException(error_msg)
    if r.headers['x-rate-limit-remaining'] == str(1):
        raise TwitterException('rate limit exceeded. try running again in 15m')


class Twitter:
    def __init__(self, twittertb):
        self.bearer_token = ""
        self.twitterdb = twittertb
        if not os.path.exists(credentials_path):
            save_credentials(credentials_path, credentials)
            error = 'create a consumer/secret key and place them in ' \
                    './twitter_credentials'
            raise TwitterException(error)
        else:
            self.credentials = load_credentials(credentials_path)

        self.bearer_token = get_application_only_token(
            self.credentials['key'],
            self.credentials['secret'])
        headers = self.get_headers()
        r = requests.get(base_api_url + 'application/rate_limit_status.json',
                         headers=headers)
        error = 'could not get rate limit status; something is very wrong'
        assert_request_success(r, 200, error)

    def get_headers(self):
        if not self.bearer_token:
            raise TwitterException('bearer_token not initialised')
        return {'Authorization': 'Bearer ' + self.bearer_token,
                'Content-Type': 'application/x-www-form-urlencoded;'
                                'charset=UTF-8'}

    def get_followed_ids(self, handle):
        ids = []
        cursor = -1
        api_path = '{0}friends/ids.json?screen_name={1}' \
            .format(base_api_url, handle)
        while not cursor == 0:
            url_with_cursor = '{0}&cursor={1}'.format(api_path, cursor)
            r = requests.get(url_with_cursor, headers=self.get_headers())
            error = "Failed to get {0}\'s follows".format(handle)
            assert_request_success(r, 200, error)
            content = json.loads(r.content)
            cursor = content['next_cursor']
            ids += content['ids']

        self.save_unknown_users(ids)
        return ids

    def save_unknown_users(self, user_ids):
        def split(l, n):
            for i in xrange(0, len(l), n):
                yield l[i:i + n]

        unknown_ids = self.twitterdb.get_unknown_user_ids(user_ids)

        for user_group in split(unknown_ids, 100):
            ids = ','.join(str(id) for id in user_group)
            api_path = '{0}users/lookup.json?user_id={1}' \
                .format(base_api_url, ids)
            r = requests.get(api_path, headers=self.get_headers())
            error = "Failed to retrive usernames for {0}".format(ids)
            assert_request_success(r, 200, error)
            content = json.loads(r.content)
            for user in content:
                self.twitterdb.add_user(User(user_id=user['id'],
                                             user_name=user['screen_name']))

    def get_tweets_until(self, user_id, target_datetime,
                         refresh_threshold=timedelta(minutes=1)):
        tweets = []
        fire_request = True
        # minimise the amount of data we pull down by seeing what's in the db
        db_tweets = self.twitterdb.get_tweets_by(user_id)
        num_tweets = len(db_tweets) > 0
        last_seen_id = db_tweets[0].id if num_tweets > 0 else 1
        last_created = db_tweets[0].date_inserted if num_tweets > 0 else \
            datetime(1900, 1, 1)
        if datetime.now() - last_created < refresh_threshold:
            logger.info('age of last tweet less than threshold; skipping')
            fire_request = False
        tweets += [t.tweet for t in db_tweets]
        min_seen_id = sys.maxint - 1
        # we want to page through the timeline until we are definite there are
        # no interesting tweets. so, if we see a tweet we care about,
        # cue up another request
        while fire_request:
            logger.info('requesting new page... with max_id = {0}'
                        .format(min_seen_id))
            fire_request = False
            new_tweets = self.get_tweets_by(user_id,
                                            since_id=last_seen_id,
                                            max_id=min_seen_id)
            for tweet in new_tweets:
                datetime_created = datetime. \
                    strptime(tweet['created_at'],
                             '%a %b %d %H:%M:%S +0000 %Y')
                if tweet['id'] < min_seen_id:
                    min_seen_id = tweet['id'] - 1
                if datetime_created >= target_datetime:
                    fire_request = True
                    db_tweet = Tweet(
                        id=tweet['id'],
                        user_id=user_id,
                        date_created=datetime_created,
                        tweet=json.dumps(tweet))
                    self.twitterdb.add_tweet(db_tweet)
                    tweets.append(tweet)
        return tweets

    def get_tweets_by(self, user_id, since_id=0, max_id=sys.maxint - 1):
        api_path = '{0}statuses/user_timeline.json?' \
                   'since_id={1}' \
                   '&max_id={2}' \
                   '&user_id={3}' \
                   '&include_rts=false' \
                   '&count=200' \
            .format(base_api_url, since_id, max_id, user_id)
        r = requests.get(api_path, headers=self.get_headers())
        # this can happen on protected streams
        if r.status_code == 401:
            logger.warning('user {0}\'s timeline is protected;'
                           ' can\'t pull tweets'.format(user_id))
            return {}
        assert_request_success(r, 200, 'Failed to get tweets for {0}'
                               .format(user_id))
        return json.loads(r.content)
