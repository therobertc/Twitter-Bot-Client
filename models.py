from flask_sqlalchemy import SQLAlchemy
from app import app


db = SQLAlchemy(app)


class CommonFields(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)


class RSSFeed(CommonFields):
    feed_url = db.Column(db.String(), nullable=False)
    checking_feed_interval = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Rss Feed Urls: {self.rss_feed_urls}"


class Retweet(CommonFields):
    handles = db.Column(db.String(), nullable=False)
    checking_timeline_interval = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Handles to Watch: {self.keywords_or_hashtags}"


class ReplyAndLike(CommonFields):
    keywords_or_hashtags = db.Column(db.String(), nullable=False)
    checking_keywords_interval = db.Column(db.Integer, nullable=False)


class Reply(ReplyAndLike):
    replies = db.Column(db.String(), nullable=False)

    def __repr__(self):
        return f"<Replies: {self.replies}"


class Like(ReplyAndLike):
    pass

    def __repr__(self):
        return f"<Like keywords: {self.keywords_or_hashtags}"
