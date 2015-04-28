from collections import defaultdict
from datetime import datetime, timedelta
import logging

import click
import tabulate

from twitter import Twitter
import twitterdb


# if the most recent tweet by a user is less than this old,
# don't bother pulling new tweets
# this is an optimisation so we don't waste api calls.
user_refresh = timedelta(hours=1)

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
    tdb = twitterdb.TwitterDB('sqlite:///{0}.db'
                              .format(handle), echo=False)

    dates = [(datetime.today() - timedelta(days=i)).date()
             for i in range(1, 8)]

    headers = ['0. user', '1. today (so far)'] + \
              [date.strftime('{0}. %a %x'.format(idx + 2))
               for idx, date in enumerate(dates)]

    today_counts = tdb.get_tweet_counts_for_date(datetime.now().date())
    columns = defaultdict(list)
    for count in today_counts:
        columns[headers[0]].append(count[0])
        columns[headers[1]].append(count[1])

    for idx, date in enumerate(dates):
        counts = tdb.get_tweet_counts_for_date(date)
        for count in counts:
            columns[headers[idx + 2]].append(count[1])

    # I'm sure there's a more sensible way of doing this
    # But tabulate doesn't want to sort the columns into a sensible order.
    rows = zip(*([key] + value for key, value in sorted(columns.items())))

    logger.info(tabulate.tabulate(rows, headers='firstrow'))


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
