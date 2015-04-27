from datetime import datetime, timedelta
from twitter import Twitter
import twitterdb
import logging

# if the most recent tweet by a user is less than this old,
# don't bother pulling new tweets
# this is an optimisation so we don't waste api calls.
user_refresh=timedelta(hours=1)


class TwitterStats:
    def __init__(self):
        pass

if __name__ == '__main__':
    logger = logging.getLogger('twitter')
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)

    # create a logging format

    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info('starting up!')

    twitter_handle = 'FodT'
    tdb = twitterdb.TwitterDB('sqlite:///{0}.db'
                              .format(twitter_handle), echo=False)
    t = Twitter(tdb)
    ids = t.get_followed_ids(twitter_handle)
    t.save_unknown_users(ids)
    one_week_ago = datetime.now() - timedelta(days=7)
    for id in ids:
        user = tdb.get_user_by_id(id)
        logger.info('getting tweets for {0}:{1}'.format(user.user_name,
                                                        user.user_id))
        t.get_tweets_until(id, one_week_ago, user_refresh)
    logger.info('done saving all the followed tweets i can!')
