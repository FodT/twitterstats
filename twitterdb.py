import sqlite3
from datetime import datetime


class TwitterDB:
    def __init__(self, connection):
        self.conn = connection
        self.c = self.conn.cursor()
        # Create tables if needed
        # keep it super simple. one table for tweets, one table for users.
        with self.conn:
            self.conn.execute('''create table if not exists users
                (id INT PRIMARY KEY,
                username TEXT)''')
            self.conn.execute('''create table if not exists tweets
                (id INT PRIMARY KEY,
                user_id INT,
                created TIMESTAMP,
                tweet TEXT)''')

    def __del__(self):
        self.conn.commit()
        self.c.close()

    def add_user(self, user_id, user_name):
        result = True
        row = [user_id, user_name]
        try:
            self.c.execute("INSERT INTO users VALUES (?, ?)", row)
        except sqlite3.Error:
            result = False
        self.conn.commit()
        return result

    def add_tweet(self, tweet_id, user_id, tweet_content, created=None):
        if not created:
            created = datetime.now()
        result = True
        row = [tweet_id, user_id, created, tweet_content]
        try:
            self.c.execute("INSERT INTO tweets VALUES (?,?,?,?)", row)
        except sqlite3.Error:
            result = False
        self.conn.commit()
        return result

    def get_user_id(self, user_name):
        result = -1
        sql = """SELECT id FROM users WHERE username = '""" \
              + user_name + """'"""
        self.c.execute(sql)
        row = self.c.fetchone()
        if row is not None:
            result = row[0]
        return result

    def get_latest_tweet_id(self, user_name="", user_id=""):
        # either search for the user ID or the userName
        # depending on which is specified.
        result = 1
        if not user_id:
            user_id = self.get_user_id(user_name)
        sql = """SELECT id FROM tweets where user_id = '""" \
              + str(user_id) \
              + """' ORDER BY id DESC"""
        self.c.execute(sql)
        row = self.c.fetchone()
        if row is not None:
            result = row[0]
        return result

    def get_tweets_by(self, user_name="",
                      user_id="",
                      date_until=None):
        if not date_until:
            date_until = datetime.now()
        # either search for the user ID or the userName
        # depending on which is specified.
        if not user_id:
            user_id = self.get_user_id(user_name)
        sql = """SELECT tweet FROM tweets where user_id = '""" \
              + str(user_id) + """' ORDER BY id DESC"""
        self.c.execute(sql)
        return self.c.fetchall()
