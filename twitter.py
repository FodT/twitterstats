import base64
import json
import os
import requests
import urllib
import sys
from datetime import datetime
from twitter_db import Tweet

credentials = {
    'key': 'GET_YOUR_OWN',
    'secret': 'GET_YOUR_OWN'}

base_api_url = 'https://api.twitter.com/1.1/'
base_oauth_url = 'https://api.twitter.com/oauth2/'

credentials_path = os.path.expanduser('twitter_credentials')


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


def assert_request_success(r, expected_code, error):
    if r.status_code != expected_code:
        content = json.loads(r.content)
        error = content['errors'][0]
        error_msg = '%s; HTTP status %d, twitter code %d, message: %s' \
                    % (error, r.status_code, error['code'], error['message'])
        raise TwitterException(error_msg)


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
        api_path = '%sfriends/ids.json?count=20&screen_name=%s' \
                   % (base_api_url, handle)
        while not cursor == 0:
            url_with_cursor = '%s&cursor=%d' % (api_path, cursor)
            r = requests.get(url_with_cursor, headers=self.get_headers())
            error = "Failed to get %s\'s follows" % handle
            assert_request_success(r, 200, error)
            content = json.loads(r.content)
            cursor = content['next_cursor']
            ids += content['ids']
        return ids

    def get_tweets_until(self, user_id, target_date):
        tweets = []
        request_again = False
        last_seen = self.twitterdb.get_latest_tweet(user_id)
        last_seen_id = 1 if not last_seen else last_seen.id
        db_tweets = self.twitterdb.get_tweets_by(user_id)
        tweets += [t.tweet for t in db_tweets]
        new_tweets = self.get_tweets_by(user_id, since_id=last_seen_id)
        for tweet in new_tweets:
            datetime_created = datetime.strptime(tweet['created_at'],
                                                 '%a %b %d %H:%M:%S +0000 %Y')
            if datetime_created.date() >= target_date:
                db_tweet = Tweet(
                    id=tweet['id'],
                    user_id=user_id,
                    date_created=datetime_created,
                    tweet=json.dumps(tweet))
                self.twitterdb.add_tweet(db_tweet)
                tweets.append(tweet)
        return tweets

    def get_tweets_by(self, user_id, since_id=0, max_id=sys.maxint-1):
        api_path = '%sstatuses/user_timeline.json?' \
                   'since_id=%d' \
                   '&max_id=%d' \
                   '&user_id=%d' \
                   '&count=200' % \
                   (base_api_url, since_id, max_id, user_id)
        r = requests.get(api_path, headers=self.get_headers())
        assert_request_success(r, 200, 'Failed to get tweets for %d' % user_id)
        return json.loads(r.content)
