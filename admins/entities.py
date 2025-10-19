from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class Message(Base):
    __tablename__ = 'admin_messages'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    tg_id = Column(db.BIGINT)
    tg_username = Column(db.String(128))
    city_id = Column(db.Integer)
    message = Column(db.Text)
    date = Column(db.DateTime, default=datetime.datetime.now)


class TGAdmin:
    def __init__(self, message):
        self.tg_id = message.tg_id
        self.tg_username = message.tg_username
        self.messages = [message]

    def __repr__(self):
        return '<TGAdmin {}>'.format(self.tg_id)