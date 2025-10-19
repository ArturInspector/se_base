from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class Link(Base):
    __tablename__ = 'links'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    code = Column(db.String(32))
    member_id = Column(db.Integer)
    link = Column(db.Text)
    city_id = Column(db.Integer)
    create_date = Column(db.DateTime, default=datetime.datetime.now)
    finish_date = Column(db.DateTime, default=None)
    status = Column(db.Integer, default=0)

    def get_status(self):
        if self.status == 0:
            return 'Активна'
        elif self.status == 1:
            return 'Переход совершен'
        elif self.status == 10:
            return 'Вступил в группу'
