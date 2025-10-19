from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class City(Base):
    __tablename__ = 'cities'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    name = Column(db.String(128))
    fias = Column(db.String(128))
    kladr = Column(db.String(128))
    group_id = Column(db.BIGINT, default=None)
    invite_link = Column(db.String(256), default=None)
    status = Column(db.Integer, default=0)
    is_test = Column(db.Boolean, default=False)

    def get_status(self):
        if self.status == 0:
            return 'Бот не подключен'
        if self.status == 1:
            return 'Бот подключен'
        if self.status == -1:
            return 'Возникла ошибка в боте'

    def __repr__(self):
        return f'City<{self.name}>'
