from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine, and_, func
from sqlalchemy.orm import sessionmaker, aliased
import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

Base = declarative_base()


class Tweet(Base):
    __tablename__ = 'tweets'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    date_created = Column(DateTime)
    date_inserted = Column(DateTime, default=datetime.now)
    tweet = Column(String)

    def __repr__(self):
        return "<Tweet(id='{0}', user_id='{1}', " \
               "date_created='{2}, date_inserted='{3}," \
               " tweet=...{3}...')>" \
            .format(self.id, self.user_id,
                    self.date_created, self.date_inserted,
                    json.loads(self.tweet)['text'])


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String)

    def __repr__(self):
        return "<User(user_id='{0}', user_name='{1}')>" \
            .format(self.user_id, self.user_name)


class TwitterDB:
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

    def add_user(self, user):
        session = self.sessionmaker()
        try:
            session.add(user)
            session.commit()

        except IntegrityError:
            session.rollback()

    def get_tweet_by_id(self, tweet_id):
        session = self.sessionmaker()
        return session.query(Tweet).filter_by(id=tweet_id).first()

    def get_user_by_id(self, user_id):
        session = self.sessionmaker()
        return session.query(User).filter_by(user_id=user_id).first()

    def get_unknown_user_ids(self, user_ids):
        session = self.sessionmaker()
        ids = session.query(User.user_id).all()
        ids = list(sum(ids, ()))

        return list(set(user_ids).difference(ids))

    def get_tweets_by(self, userid, date_until=datetime(1900, 1, 1)):
        session = self.sessionmaker()
        return session.query(Tweet).filter(
            and_(Tweet.user_id == userid,
                 Tweet.date_created >= date_until)). \
            order_by(Tweet.id.desc()).all()

    def get_tweet_counts_for_date(self, for_date=None):
        if not for_date:
            for_date = datetime.now().date()
        session = self.sessionmaker()

        tally_subq = session.query(
            Tweet.user_id,
            func.count(Tweet.user_id).label('tally')). \
            filter(func.date(Tweet.date_created) == for_date). \
            group_by(Tweet.user_id).subquery()

        return session.query(User.user_name,
                             func.ifnull(tally_subq.c.tally, 0))\
            .select_from(User)\
            .outerjoin(tally_subq, tally_subq.c.user_id == User.user_id)\
            .order_by(User.user_name).all()
