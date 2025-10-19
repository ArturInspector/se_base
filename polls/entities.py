from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class Poll(Base):
    __tablename__ = 'polls'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    question = Column(db.String(100))
    options = Column(db.JSON, default=[])
    is_anonymous = Column(db.Boolean)
    tg_ids = Column(db.JSON, default={})
    create_date = Column(db.DateTime, default=datetime.datetime.now)


class TGPoll(Base):
    __tablename__ = 'tg_polls'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    poll_id = Column(db.String(64))
    city_id = Column(db.Integer)
    city_name = Column(db.String(128))
    parent_id = Column(db.Integer)
    options = Column(db.JSON, default={})
    create_date = Column(db.DateTime, default=datetime.datetime.now)