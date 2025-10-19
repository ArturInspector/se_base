from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class TGUser(Base):
    __tablename__ = 'notifications_users'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    tg_id = Column(db.BIGINT)