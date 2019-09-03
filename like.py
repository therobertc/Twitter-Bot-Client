from twython import Twython, TwythonError
import time
import random
import ast
import json


def like_func(keywords, twitter):

    for word in keywords:
        search_results = twitter.search(
            q=word + "-filter:retweets AND -filter:replies", count=3, lang="en", result_type="recent")

        for tweet in search_results["statuses"]:
            tweet_text = tweet.get('text')
            if tweet_text[0] != "@" and "RT" not in tweet_text and tweet_text.count("#") <= 3:
                try:
                    tweet_id = tweet.get('id')
                    twitter.create_favorite(id=tweet_id)
                    print("Tweet liked")
                    time.sleep(random.choice(list(range(10, 31))))
                except TwythonError as e:
                    print(e)
