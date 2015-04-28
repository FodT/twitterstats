from datetime import datetime, timedelta
from twitter import Twitter
import twitterdb
import logging
import click

# if the most recent tweet by a user is less than this old,
# don't bother pulling new tweets
# this is an optimisation so we don't waste api calls.
user_refresh=timedelta(hours=1)


logger = logging.getLogger('twitter')
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


@click.group(chain=False)
def cli():
    pass


@cli.command(name='show-stats')
@click.argument('handle')
def show_stats(handle):
    logger.info('generating stats report for {0}'.format(handle))


@cli.command(name='get-tweets')
@click.argument('handle')
def update_tweets(handle):
    logger.info('updating tweets for users followed by {0}'
                .format(handle))

    tdb = twitterdb.TwitterDB('sqlite:///{0}.db'
                              .format(handle), echo=False)
    t = Twitter(tdb)
    ids = t.get_followed_ids(handle)
    t.save_unknown_users(ids)
    one_week_ago = datetime.now() - timedelta(days=7)
    for id in ids:
        user = tdb.get_user_by_id(id)
        logger.info('Getting tweets for {0}:{1}'.format(user.user_name,
                                                        user.user_id))
        t.get_tweets_until(id, one_week_ago, user_refresh)
    logger.info('Done saving all the followed tweets I can!')


if __name__ == '__main__':
    cli()
