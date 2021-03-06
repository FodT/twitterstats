import json
import twitterdb
from twitterdb import Tweet, User
import unittest
from datetime import datetime


with open('test/fixtures/tweets_apr_23_2015.json') as f:
    tweet_fixture = json.load(f)


class TestDBFunctions(unittest.TestCase):
    def setUp(self):
        self.db = twitterdb.TwitterDB('sqlite:///:memory:', echo=True)

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

    def testGetAllTweetCountsForDate(self):
        date1 = datetime(2015, 3, 1, 1, 2, 3)
        date2 = datetime(2015, 3, 2, 1, 3, 4)
        date2_1 = datetime(2015, 3, 2, 1, 3, 5)
        date3 = datetime(2015, 4, 3, 11, 3, 2)
        tweet1 = Tweet(id=1, user_id=1,
                       date_created=date1,
                       tweet=json.dumps(tweet_fixture[0]))
        tweet2 = Tweet(id=2, user_id=1,
                       date_created=date2,
                       tweet=json.dumps(tweet_fixture[1]))

        tweet3 = Tweet(id=3, user_id=1,
                       date_created=date2_1,
                       tweet=json.dumps(tweet_fixture[2]))

        tweet4 = Tweet(id=4, user_id=1,
                       date_created=date3,
                       tweet=json.dumps(tweet_fixture[2]))

        tweet5 = Tweet(id=5, user_id=2,
                       date_created=date3,
                       tweet=json.dumps(tweet_fixture[2]))

        self.db.add_user(User(user_id=1, user_name='aaron'))
        self.db.add_user(User(user_id=2, user_name='bob'))
        self.db.add_tweet(tweet1)
        self.db.add_tweet(tweet2)
        self.db.add_tweet(tweet3)
        self.db.add_tweet(tweet4)
        self.db.add_tweet(tweet5)

        tweet_tallies = self.db.get_tweet_counts_for_date(date2.date())

        self.assertEqual(tweet_tallies[0][1], 2)

    def testAddUser(self):
        user = User(user_id=1, user_name='name')
        self.db.add_user(user)

        saved_user = self.db.get_user_by_id(1)
        self.assertEqual(saved_user.user_id, 1)
        self.assertEqual(saved_user.user_name, 'name')

    def testAddSameUser(self):
        user1 = User(user_id=1, user_name='name')
        user2 = User(user_id=1, user_name='differentName')
        self.db.add_user(user1)
        self.db.add_user(user2)

        saved_user = self.db.get_user_by_id(1)
        self.assertEqual(saved_user.user_id, 1)
        self.assertEqual(saved_user.user_name, 'name')

    def testGetUnknownUserIds(self):
        user1 = User(user_id=1, user_name='name')
        user2 = User(user_id=2, user_name='differentName')
        self.db.add_user(user1)
        self.db.add_user(user2)
        ids = self.db.get_unknown_user_ids([1, 2, 3, 4])
        self.assertEqual(ids, [3, 4])
