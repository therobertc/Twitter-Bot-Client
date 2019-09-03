import feedparser
import time
from pprint import pprint


def tweet_from_rss_feed(urls, twitter_api):

    for url in urls:
        feed = feedparser.parse(url)
        post = feed.entries[0]
        title = post.title
        link = post.link
        status = f"{title}\n\n{link}"
        try:
            twitter_api.update_status(status=status)
            print("Tweet from rss feed successfully sent!")
            time.sleep(30)
        except Exception as e:
            print(e)
