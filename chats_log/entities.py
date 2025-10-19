from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class ChatLog(Base):
    __tablename__ = 'chats_logs'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    webhook_id = Column(db.String(64))
    message_id = Column(db.String(64))
    chat_id = Column(db.String(64))
    user_id = Column(db.Integer)
    author_id = Column(db.Integer)
    created_at = Column(db.DateTime)
    message = Column(db.Text)
    create_date = Column(db.DateTime, default=datetime.datetime.now)
    is_success = Column(db.Boolean, default=True)
    answer = Column(db.Text, default='')
    comment = Column(db.Text)