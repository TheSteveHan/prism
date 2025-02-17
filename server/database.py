from datetime import datetime
from enum import IntEnum
from .settings import db, admin
from flask_admin.contrib.sqla import ModelView
from dataclasses import dataclass
from sqlalchemy.dialects.postgresql import insert as pg_insert



class PostModality(IntEnum):
    TXT = 0
    VIDEO = 1

@dataclass
class Post(db.Model):
    id:int = db.Column(db.Integer, primary_key=True)
    uri:str = db.Column(db.String, index=True, nullable=False)
    cid = db.Column(db.String, nullable=True)
    reply_parent = db.Column(db.String, nullable=True, default=None)
    reply_root = db.Column(db.String, nullable=True, default=None)
    indexed_at:str = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    e_score:float = db.Column(db.Float, nullable=True, default=None)
    e_conf = db.Column(db.Float, nullable=True, default=None)
    i_score:float = db.Column(db.Float, nullable=True, default=None)
    i_conf = db.Column(db.Float, nullable=True, default=None)
    a_score:float = db.Column(db.Float, nullable=True, default=None)
    a_conf = db.Column(db.Float, nullable=True, default=None)
    text:str = db.Column(db.String, nullable=True)
    modality:int = db.Column(db.Integer, nullable=True, index=True)
    approved = db.Column(db.Boolean, nullable=True, index=True)


    def __repr__(self):
        return f"<Post {self.id} - {self.uri}>"

@dataclass
class PostSubmission(db.Model):
    __defailt_unique_constraint_name__ = "uq_post_submission_uri"
    id:int = db.Column(db.Integer, primary_key=True)
    uri:str = db.Column(db.String, nullable=False, unique=True)
    text:str = db.Column(db.String, nullable=True)
    data:dict = db.Column(db.JSON, nullable=True)
    videos:dict = db.Column(db.JSON, nullable=True)
    submitter:str = db.Column(db.String, index=True, nullable=False)
    submitted_at:str = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = db.Column(db.DateTime, nullable=True)

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
    RECOMMENDABLE = 4

class Label(db.Model):
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    label_type = db.Column(db.Integer, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    src = db.Column(db.String, nullable=False)
    value = db.Column(db.Float, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    post_id = db.Column(db.BigInteger, db.ForeignKey('post.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=True, )
    comment = db.Column(db.String, nullable=True)

    post = db.relationship('Post', backref='labels')

    __table_args__ = (
        db.Index('idx_label_type_confidence_post_id', 'label_type', 'confidence', 'post_id'),
    )

admin.add_view(ModelView(PostSubmission, db.session))
admin.add_view(ModelView(Post, db.session))
admin.add_view(ModelView(Label, db.session))


def upsert_update_constraint(model, objects, params=None, db_engine=None):
    if not params:
        params = {
            'constraint': model.__defailt_unique_constraint_name__
        }
    obj_dicts = []
    # all of the keys that should be updated on conflict
    update_keys= set()
    for obj in objects:
        props = dict(obj.__dict__) if not isinstance(obj, dict) else obj
        props.pop("_sa_instance_state", None)
        obj_dicts.append(props)
        update_keys.update(props)
    if not update_keys:
        return
    statement = pg_insert(model).values(obj_dicts)
    params.update({
        "set_":{
            key: getattr(statement.excluded, key)
            for key in update_keys
        }
    })
    statement = statement.on_conflict_do_update(**params)
    if not db_engine:
        db.session.execute(statement)
        db.session.commit()
    else:
        db_engine.execute(statement)

def upsert_ignore_constraint(model, objects, params=None):
    if params is None:
        params = {
            'constraint': model.__defailt_unique_constraint_name__
        }
    obj_dicts = []
    for obj in objects:
        props = dict(obj.__dict__)
        props.pop("_sa_instance_state")
        obj_dicts.append(props)
    statement = pg_insert(model).values(obj_dicts).on_conflict_do_nothing(
        **params
    )
    db.session.execute(statement)
    db.session.commit()

