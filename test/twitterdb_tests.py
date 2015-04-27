import twitterdb
import unittest
import sqlite3
from datetime import datetime


class TestDBFunctions(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:', detect_types=sqlite3.PARSE_DECLTYPES + sqlite3.PARSE_COLNAMES)
        self.tdb = twitterdb.TwitterDB(self.conn)
        self.c = self.conn.cursor()

    def tearDown(self):
        self.tdb = None
        sql = """DELETE FROM 'users'"""
        self.c.execute(sql)
        self.conn.commit()
        sql = """DELETE FROM 'tweets'"""
        self.c.execute(sql)
        self.conn.commit()

    def setup(self):
        self.setUp()

    def teardown(self):
        self.tearDown()

    def test_tablesExist(self):
        usersql = """select count(type) from sqlite_master where type='table' and name='users'"""
        tweetsql = """select count(type) from sqlite_master where type='table' and name='tweets'"""
        self.c.execute(usersql)
        self.assertEqual(self.c.fetchone()[0], 1)
        self.c.execute(tweetsql)
        self.assertEqual(self.c.fetchone()[0], 1)

    def test_add_user(self):
        self.tdb.add_user(123456, "Fod")
        sql = """select * from users where username = 'Fod'"""
        self.c.execute(sql)
        row = self.c.fetchone()
        self.assertEqual(row[0], 123456)
        self.assertEqual(row[1], "Fod")

    def test_add_same_user(self):
        self.tdb.add_user(123456, "Fod")
        self.assertEqual(self.tdb.add_user(123456, "FodDupe"), False)

    def test_add_tweet(self):
        now = datetime.now()
        self.tdb.add_tweet(1, 123456, "Hello this is Fod", now)
        self.tdb.add_tweet(2, 123456, "Hello this is Fod1", now)
        self.tdb.add_tweet(3, 123456, "Hello this is Fod2", now)
        sql = """select * from tweets where user_id = 123456"""
        self.c.execute(sql)
        rows = self.c.fetchall()
        self.assertEqual(rows[0][0], 1)
        self.assertEqual(rows[0][1], 123456)
        self.assertEqual(rows[0][2], now)
        self.assertEqual(rows[0][3], "Hello this is Fod")
        self.assertEqual(rows[1][0], 2)
        self.assertEqual(rows[1][2], now)
        self.assertEqual(rows[1][1], 123456)
        self.assertEqual(rows[1][3], "Hello this is Fod1")
        self.assertEqual(rows[2][0], 3)
        self.assertEqual(rows[2][1], 123456)
        self.assertEqual(rows[2][2], now)
        self.assertEqual(rows[2][3], "Hello this is Fod2")

    def test_add_same_tweet(self):
        self.tdb.add_tweet(1, 123456, "Hello this is Fod")
        self.assertEqual(
            self.tdb.add_tweet(
                1,
                123456,
                "Different tweet with same ID! Invalid",
                datetime.now()), False)

    def test_get_user_id(self):
        self.tdb.add_user(123456, "Fod")
        id = self.tdb.get_user_id("Fod")
        self.assertEqual(id, 123456)

    def test_get_user_id_nonexistent(self):
        id = self.tdb.get_user_id("IWontExist")
        self.assertEqual(id, -1)

    def test_get_last_tweet_id(self):
        self.tdb.add_tweet(1, 123456, "Hello this is my first tweet")
        self.tdb.add_tweet(4, 333333,
                           "Hello this is someone completely different")
        self.tdb.add_tweet(2, 123456,
                           "Hello this is my latest tweet")
        id = self.tdb.get_latest_tweet_id(user_id=123456)

        sql = """select * from tweets"""
        self.c.execute(sql)
        rows = self.c.fetchall()
        self.assertEqual(id, 2)

    def test_get_last_tweet_id_no_tweets(self):
        id = self.tdb.get_latest_tweet_id(user_id=123456)
        self.assertEqual(id, 1)

    def test_get_last_tweet_id_from_user_name(self):
        self.tdb.add_user(123456, "Fod")
        self.tdb.add_user(333333, "SomeoneElse")
        self.tdb.add_tweet(1, 123456, "Hello this is my first tweet")
        self.tdb.add_tweet(4, 333333,
                           "Hello this is someone completely different")
        self.tdb.add_tweet(2, 123456, "Hello this is my latest tweet")
        id = self.tdb.get_latest_tweet_id(user_name="Fod")

        sql = """select * from tweets"""
        self.c.execute(sql)
        rows = self.c.fetchall()
        self.assertEqual(id, 2)


if __name__ == '__main__':
    unittest.main()
