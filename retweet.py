from twython import Twython, TwythonError
import time
import random


def retweet_func(handles, api):

    for handle in handles:
        timeline_tweet = api.get_user_timeline(
            screen_name=handle, count=1, include_rts=False, exclude_replies=True)
        tweet_id = timeline_tweet.get('id')
        api.retweet(id=tweet_id)
        print("Tweet retweeted!")
        time.sleep(random.choice(list(range(10, 30))))
