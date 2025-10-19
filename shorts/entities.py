from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class Short(Base):
    __tablename__ = 'shorts'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    name = Column(db.String(128))
    link = Column(db.String(64))
    is_removed = Column(db.Boolean, default=False)


class Visit(Base):
    __tablename__ = 'visits'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    short_id = Column(db.Integer)
    link = Column(db.String(64))
    date = Column(db.DateTime, default=datetime.datetime.now)