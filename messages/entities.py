from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class Message(Base):
    __tablename__ = 'messages'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    token = Column(db.String(64))
    dialog_id = Column(db.Integer)
    dialog_token = Column(db.String(64))
    is_system = Column(db.Boolean)
    text = Column(db.Text)
    buttons = Column(db.JSON)
    date = Column(db.DateTime, default=datetime.datetime.now)