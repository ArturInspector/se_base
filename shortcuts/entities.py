from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class Message(Base):
    __tablename__ = 'whatsapp_messages'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    phone = Column(db.String(16))
    message = Column(db.Text)
    is_business = Column(db.Boolean, default=False)
    create_date = Column(db.DateTime, default=datetime.datetime.now)
    finish_date = Column(db.DateTime, default=None)
    is_send = Column(db.Boolean, default=False)

    def to_shortcut_model(self):
        model = {
            'status': 1,
            'id': self.id,
            'phone': '+7' + self.phone,
            'message': self.message,
            'is_business': self.is_business
        }
        return model


class TaskNotify(Base):
    __tablename__ = 'tasks_notifications'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    member_status = Column(db.Integer)
    minutes = Column(db.Integer)
    message = Column(db.Text)