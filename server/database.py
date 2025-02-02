from datetime import datetime
from enum import IntEnum
from .settings import db

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uri = db.Column(db.String, index=True, nullable=False)
    cid = db.Column(db.String, nullable=False)
    reply_parent = db.Column(db.String, nullable=True, default=None)
    reply_root = db.Column(db.String, nullable=True, default=None)
    indexed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    e_score = db.Column(db.Float, nullable=True, default=None, index=True)
    e_conf = db.Column(db.Float, nullable=True, default=None, index=True)
    i_score = db.Column(db.Float, nullable=True, default=None, index=True)
    i_conf = db.Column(db.Float, nullable=True, default=None, index=True)
    a_score = db.Column(db.Float, nullable=True, default=None, index=True)
    a_conf = db.Column(db.Float, nullable=True, default=None, index=True)
    text = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f"<Post {self.id} - {self.uri}>"


class SubscriptionState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String, unique=True, nullable=False)
    cursor = db.Column(db.BigInteger, nullable=False)

    def __repr__(self):
        return f"<SubscriptionState {self.service} - {self.cursor}>"

class LabelType(IntEnum):
    EMOTION_28 = 0
    EMOTION_AGG = 1
    INTELLECTUAL = 2
    ACTIONABLE = 3

class Label(db.Model):
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    label_type = db.Column(db.Integer, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    src = db.Column(db.String, nullable=False)
    value = db.Column(db.Float, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    post_id = db.Column(db.BigInteger, db.ForeignKey('post.id'), nullable=False)

    post = db.relationship('Post', backref='labels')

    __table_args__ = (
        db.Index('idx_label_type_confidence_post_id', 'label_type', 'confidence', 'post_id'),
    )

