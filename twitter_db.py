from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime


Base = declarative_base()


class Tweet(Base):
    __tablename__ = 'tweets'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    date_created = Column(DateTime)
    tweet = Column(String)

    def __repr__(self):
        return "<Tweet(id='{0}', user_id='{1}', " \
               "date_created='{2}, tweet=...{3}...')>"\
            .format(self.id, self.user_id,
                    self.date_created, json.loads(self.tweet)['text'])


class Twitter_DB:
    def __init__(self, database, echo=False):

        self.engine = create_engine(database)

        self.sessionmaker = sessionmaker()
        self.sessionmaker.configure(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def add_tweet(self, tweet):
        session = self.sessionmaker()
        try:
            session.add(tweet)
            session.commit()

        except IntegrityError:
            session.rollback()

    def get_tweet_by_id(self, tweet_id):
        session = self.sessionmaker()
        return session.query(Tweet).filter_by(id=tweet_id).first()

    def get_latest_tweet_id(self, userid):
        session = self.sessionmaker()
        latest = session.query(Tweet).filter_by(user_id=userid). \
            order_by(Tweet.id.desc()).first()
        return 1 if not latest else latest.id

    def get_tweets_by(self, userid, date_until=None):
        if not date_until:
            date_until = datetime(1900, 1, 1)
        session = self.sessionmaker()
        return session.query(Tweet).filter(
            and_(Tweet.user_id == userid,
                 Tweet.date_created >= date_until)). \
            order_by(Tweet.id.desc()).all()
