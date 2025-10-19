from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class SpamBlock(Base):
    __tablename__ = 'spam_blocks'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    tg_id = Column(db.BIGINT)
    tg_username = Column(db.String(64), default=None)
    tg_first_name = Column(db.String(64), default=None)
    tg_last_name = Column(db.String(64), default=None)
    tg_group_id = Column(db.BIGINT)
    tg_group_name = Column(db.String(128))
    message = Column(db.Text)
    words_list = Column(db.JSON, default=[])
    date = Column(db.DateTime, default=datetime.datetime.now)
    is_success = Column(db.Boolean)
    error = Column(db.Text, default=None)