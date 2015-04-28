# twitterstats

Simple tool to pull tweets and do some kind of analysis to. 
Probably just 'num of tweets per user per day'.


it's a work in progress.


Known issues:
* can't pull tweets from protected timelines, but will generate false 'zero' stats for them.
* will hit the twitter rate limit when populating the database when run for a new user with a moderate (>100) number of friends. Cant really do anything about this; It will pick up where it left off when you re-run after the window resets.
* doesn't really deal with unfollowed users - it will only add new users as they are followed. could resolve with a housekeeping function to delete no longer followed users, but requires more thought to implement a robust solution
* generating the stats takes a while (doing one db query per day per user followed) - should look into optimising that.

Dependencies:
* requests
* httmock
* tabulate
* click
* sqlalchemy