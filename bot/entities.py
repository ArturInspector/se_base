from telebot.types import Message
from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class TGUser(Base):
    __tablename__ = 'tg_users'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    tg_id = Column(db.BIGINT)


class TGMessage:
    def __init__(self, message: Message, source_code=None):
        self.msg_id = message.message_id
        self.tg_id = message.chat.id
        self.text = message.text
        self.source_code = source_code