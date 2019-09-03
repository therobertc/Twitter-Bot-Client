import random
import time

from apscheduler.schedulers.background import BackgroundScheduler
from flask import (Flask, current_app, flash, redirect, render_template,
                   request, session, url_for)
from flask_dance.contrib.twitter import make_twitter_blueprint, twitter
from flask_sqlalchemy import SQLAlchemy
from twython import Twython, TwythonError

from like import like_func
from reply import reply_func
from retweet import retweet_func
from rssfeedparser import tweet_from_rss_feed


app = Flask(__name__)
app.secret_key = b'ef2d9e42b968c1d2aba324b1b893545e945e9c69'
app.config["SQLALCHEMY_DATABASE_URI"] = "DATABASE URL"
scheduler = BackgroundScheduler()
scheduler.start()

CONSUMER_KEY = "CONSUMER_KEY"
CONSUMER_SECRET = "CONSUMER_SECRET"

blueprint = make_twitter_blueprint(
    api_key=CONSUMER_KEY,
    api_secret=CONSUMER_SECRET,
)
app.register_blueprint(blueprint, url_prefix="/login")


# db models
db = SQLAlchemy(app)


class RSSFeed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    feed_url = db.Column(db.String(1000))
    checking_feed_interval = db.Column(db.Integer)

    def __repr__(self):
        return f"Rss Feed Urls: {self.feed_urls}"


class Retweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    handles = db.Column(db.String(10000))
    checking_timeline_interval = db.Column(db.Integer)

    def __repr__(self):
        return f"<Handles to Watch: {self.checking_timeline_interval}"


# class ReplyAndLike(CommonFields):
#     keywords_or_hashtags = db.Column(db.String(1000))
#     checking_keywords_interval = db.Column(db.Integer)


class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    keywords_or_hashtags = db.Column(db.String(1000))
    checking_keywords_interval = db.Column(db.Integer)
    replies = db.Column(db.String(1000))

    def __repr__(self):
        return f"<Replies: {self.replies}"


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    keywords_or_hashtags = db.Column(db.String(1000))
    checking_keywords_interval = db.Column(db.Integer)

    def __repr__(self):
        return f"<Like keywords: {self.keywords_or_hashtags}"


def twitter_api():
    oauth_token = blueprint.session.token.get('oauth_token')
    oauth_token_secret = blueprint.session.token.get('oauth_token_secret')
    api = Twython(CONSUMER_KEY, CONSUMER_SECRET,
                  oauth_token, oauth_token_secret)
    return api


def tweet(status=None):
    api = twitter_api()
    try:
        api.update_status(status=status)
        print("Tweet Successfully sent!")
    except TwythonError as e:
        print(e)


@app.route("/")
def index():
    if not twitter.authorized:
        return render_template('login.html')
    return render_template('dashboard.html')


@app.route("/twitter_login")
def twitter_login():
    if not twitter.authorized:
        print(session)
        return redirect(url_for('twitter.login'))
    resp = twitter.get("account/verify_credentials.json")
    print(resp.json())
    assert resp.ok
    flash(f"You are successfully Logged in as @{resp.json()['screen_name']}")
    return render_template('dashboard.html')


@app.route("/retweet")
def retweet():
    name = blueprint.session.token.get('screen_name')
    if request.method == "POST":
        TWITTER_API = twitter_api()
        handles = [handle.replace("\r", "").strip() for handle in request.form.get(
            "handles_to_watch").split("\n")]

        time_interval_to_check_timeline = int(request.form.get(
            "checking_timeline_interval"))

        retweet = Retweet.query.filter_by(username=name).first()
        if retweet:
            retweet.handles = handles
            retweet.checking_keywords_interval = time_interval_to_check_timeline
            db.session.add(retweet)
            db.session.commit()
        else:
            retweet = Retweet(
                username=name, checking_timeline_interval=time_interval_to_check_timeline)
            db.session.add(retweet)
            db.session.commit()

        scheduler.add_job(retweet_func, 'interval', seconds=time_interval_to_check_timeline,
                          args=(handles, TWITTER_API))

        return redirect(url_for('bot_status'))
    return render_template('retweet.html')


@app.route("/bot_status", methods=["GET", "POST"])
def bot_status():
    name = blueprint.session.token.get('screen_name')

    retweet = Retweet.query.filter_by(username=name).first()
    if retweet:
        retweet_obj = {
            "handles": retweet.handles,
            "interval": retweet.checking_timeline_interval
        }
    else:
        retweet_obj = None

    reply = Reply.query.filter_by(username=name).first()
    if reply:
        reply_obj = {
            "keywords_or_hashtags": reply.keywords_or_hashtags,
            "replies": reply.replies,
            "checking_keywords_interval": reply.checking_keywords_interval
        }
    else:
        reply_obj = None

    like = Like.query.filter_by(username=name).first()
    if like:
        like_obj = {
            "keywords_or_hashtags": like.keywords_or_hashtags,
            "checking_keywords_interval": like.checking_keywords_interval
        }
    else:
        like_obj = None

    rssfeed = RSSFeed.query.filter_by(username=name).first()
    if rssfeed:
        rssfeed_obj = {
            "rssfeed_url": rssfeed.feed_url,
            "checking_feed_interval": rssfeed.checking_feed_interval,
        }
    else:
        rssfeed_obj = None

    return render_template("bot_status.html", retweet=retweet_obj,
                           reply=reply_obj, like=like_obj, rssfeed=rssfeed_obj)


@app.route("/login", methods=['GET', 'POST'])
def login():
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    scheduler.shutdown(wait=False)
    return redirect(url_for("login"))


@app.route("/rssfeed", methods=["GET", "POST"])
def rssfeed():
    if request.method == "POST":
        TWITTER_API = twitter_api()
        rss_feed_urls = [url.replace("\r", "").strip(
        ) for url in request.form.get("rss_feed_urls").split("\n")]

        interval_between_checking_rss_feed = int(request.form.get(
            "time_interval_for_rss_feed"))
        # print(interval_between_checking_rss_feed)

        scheduler.add_job(tweet_from_rss_feed, 'interval', minutes=interval_between_checking_rss_feed,
                          args=(rss_feed_urls, TWITTER_API))

        return render_template('rssfeed.html')
    return render_template('rssfeed.html')


@app.route("/dashboard")
def dashboard():

    return render_template("dashboard.html")


@app.route("/like", methods=["GET", "POST"])
def like_tweet():
    name = blueprint.session.token.get('screen_name')
    if request.method == "POST":
        TWITTER_API = twitter_api()
        keywords = [keyword.replace("\r", "").strip() for keyword in request.form.get(
            "keywords_to_watch").split("\n")]

        time_interval_to_check_keywords = int(request.form.get(
            "time_interval_to_check_keywords"))

        like = Like.query.filter_by(username=name).first()
        if like:
            like.keywords_or_hashtags = keywords
            like.checking_keywords_interval = time_interval_to_check_keywords
            db.session.add(like)
            db.session.commit()
        else:
            like = Like(username=name, keywords_or_hashtags=keywords,
                        checking_keywords_interval=time_interval_to_check_keywords)
            db.session.add(like)
            db.session.commit()

        scheduler.add_job(like_func, 'interval', minutes=time_interval_to_check_keywords,
                          args=(keywords, TWITTER_API))

        return redirect(url_for('bot_status'))
    return render_template("like.html")


@app.route("/reply", methods=["GET", "POST"])
def reply_tweet():
    name = blueprint.session.token.get('screen_name')
    if request.method == "POST":
        TWITTER_API = twitter_api()
        keywords = [keyword.replace("\r", "").strip() for keyword in request.form.get(
            "keywords_to_watch").split("\n")]

        replies = [reply.replace("\r", "").strip() for reply in request.form.get(
            "replies").split("\n")]

        reply = Reply.query.filter_by(username=name).first()
        if reply:
            reply.keywords_or_hashtags = keywords
            reply.replies = replies
            db.session.add(reply)
            db.session.commit()
        else:
            reply = Reply(username=name, keywords_or_hashtags=keywords,
                          replies=replies, checking_keywords_interval=None)
            db.session.add(reply)
            db.session.commit()

        schedule_time_to_reply = int(request.form.get(
            "schedule_time_to_reply"))

        scheduler.add_job(reply_func, 'interval', minutes=schedule_time_to_reply,
                          args=(keywords, replies, TWITTER_API))

        return redirect(url_for('bot_status'))
    return render_template("reply.html")


if __name__ == "__main__":
    app.run(debug=False)
