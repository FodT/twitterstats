import json
import twitter_db
from twitter_db import Tweet
import unittest
from datetime import datetime


with open('test/fixtures/tweets_apr_23_2015.json') as f:
    tweet_fixture = json.load(f)


class TestDBFunctions(unittest.TestCase):
    def setUp(self):
        self.db = twitter_db.Twitter_DB('sqlite:///:memory:', echo=True)

    def testTweetInitialised(self):
        expected_date = datetime.now()
        tweet = Tweet(id=1, user_id=2,
                      date_created=expected_date,
                      tweet=json.dumps(tweet_fixture[0]))
        self.assertEqual(tweet.id, 1)
        self.assertEqual(tweet.user_id, 2)
        self.assertEqual(tweet.date_created, expected_date)
        self.assertEqual(tweet.tweet, json.dumps(tweet_fixture[0]))

    def testAddTweet(self):
        expected_date = datetime.now()
        tweet = Tweet(id=1, user_id=2,
                      date_created=expected_date,
                      tweet=json.dumps(tweet_fixture[0]))
        self.db.add_tweet(tweet)

        saved_tweet = self.db.get_tweet_by_id(1)
        self.assertEqual(saved_tweet.id, 1)
        self.assertEqual(saved_tweet.user_id, 2)
        self.assertEqual(saved_tweet.date_created, expected_date)
        self.assertEqual(saved_tweet.tweet, json.dumps(tweet_fixture[0]))

    def testAddSameTweet(self):
        expected_date = datetime.now()
        tweet1 = Tweet(id=1, user_id=2,
                       date_created=expected_date,
                       tweet=json.dumps(tweet_fixture[0]))
        tweet2 = Tweet(id=1, user_id=2,
                       date_created=expected_date,
                       tweet=json.dumps(tweet_fixture[1]))
        self.db.add_tweet(tweet1)
        self.db.add_tweet(tweet2)
        saved_tweet = self.db.get_tweet_by_id(1)

        self.assertEqual(saved_tweet.tweet, json.dumps(tweet_fixture[0]))

    def testGetLatestTweet(self):
        tweet1 = Tweet(id=1, user_id=1,
                       date_created=datetime.now(),
                       tweet=json.dumps(tweet_fixture[0]))
        tweet2 = Tweet(id=2, user_id=1,
                       date_created=datetime.now(),
                       tweet=json.dumps(tweet_fixture[1]))

        tweet3 = Tweet(id=3, user_id=1,
                       date_created=datetime.now(),
                       tweet=json.dumps(tweet_fixture[2]))

        tweet4 = Tweet(id=6, user_id=2,
                       date_created=datetime.now(),
                       tweet=json.dumps(tweet_fixture[1]))

        self.db.add_tweet(tweet1)
        self.db.add_tweet(tweet2)
        self.db.add_tweet(tweet3)
        self.db.add_tweet(tweet4)

        latest1 = self.db.get_latest_tweet(1)
        latest2 = self.db.get_latest_tweet(2)

        self.assertEqual(latest1.id, 3)
        self.assertEqual(latest2.id, 6)

    def test_get_last_tweet_no_tweets(self):
        latest = self.db.get_latest_tweet(123456)
        self.assertEqual(latest, None)

    def testGetTweetsBy(self):
        tweet1 = Tweet(id=1, user_id=1,
                       date_created=datetime.now(),
                       tweet=json.dumps(tweet_fixture[0]))
        tweet2 = Tweet(id=2, user_id=1,
                       date_created=datetime.now(),
                       tweet=json.dumps(tweet_fixture[1]))

        tweet3 = Tweet(id=3, user_id=1,
                       date_created=datetime.now(),
                       tweet=json.dumps(tweet_fixture[2]))

        tweet4 = Tweet(id=6, user_id=2,
                       date_created=datetime.now(),
                       tweet=json.dumps(tweet_fixture[1]))

        self.db.add_tweet(tweet1)
        self.db.add_tweet(tweet2)
        self.db.add_tweet(tweet3)
        self.db.add_tweet(tweet4)

        tweets = self.db.get_tweets_by(1)

        self.assertEqual(len(tweets), 3)
        self.assertEqual(tweets[0].id, 3)

    def testGetTweetsByWithDate(self):
        past_date = datetime(2015, 3, 1)
        now_date = datetime.now()
        tweet1 = Tweet(id=1, user_id=1,
                       date_created=past_date,
                       tweet=json.dumps(tweet_fixture[0]))
        tweet2 = Tweet(id=2, user_id=1,
                       date_created=now_date,
                       tweet=json.dumps(tweet_fixture[1]))

        self.db.add_tweet(tweet1)
        self.db.add_tweet(tweet2)

        in_between_date = datetime(2015, 4, 1)

        now_tweets = self.db.get_tweets_by(1, now_date)
        intermediate_tweets = self.db.get_tweets_by(1, in_between_date)

        self.assertEqual(len(now_tweets), 1)
        self.assertEqual(len(intermediate_tweets), 1)
        self.assertEqual(now_tweets[0].id, 2)
        self.assertEqual(intermediate_tweets[0].id, 2)
