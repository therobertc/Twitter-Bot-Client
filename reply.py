from twython import Twython, TwythonError
import time
import random


def reply_func(keywords, replies, twitter):
    for word in keywords:
        search_results = twitter.search(
            q=word + "-filter:retweets AND -filter:replies", count=2, lang="en", result_type="recent")
        try:
            for tweet in search_results["statuses"]:
                tweet_text = random.choice(replies)
                text = tweet.get('text')
                handle = tweet.get('user').get('screen_name')
                if text[0] != "@" and "RT" not in text and text.count("#") <= 3:
                    try:
                        tweet_id = tweet.get('id')
                        twitter.update_status(
                            status=f"@{handle} {tweet_text}", in_reply_to_status_id=tweet_id)
                        print("Reply sent")
                        time.sleep(random.choice(list(range(20, 30))))
                        # time.sleep(30)
                    except TwythonError as e:
                        print(e)
        except TwythonError as e:
            print("something went wrong because", e)
