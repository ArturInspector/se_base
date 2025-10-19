from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class User(Base):
    """
    Класс-описание пользователя
    """
    __tablename__ = 'users'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    login = Column(db.String(64))
    password = Column(db.String(64))
    create_date = Column(db.DateTime, default=datetime.datetime.now)