from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class Member(Base):
    __tablename__ = 'members'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = Column(db.String(64))
    phone = Column(db.String(64), default='')
    surname = Column(db.String(64), default='')
    name = Column(db.String(64), default='')
    second_name = Column(db.String(64), default='')
    city_id = Column(db.Integer, default=0)
    status = Column(db.Integer, default=0)
    create_date = Column(db.DateTime, default=datetime.datetime.now)
    last_update = Column(db.DateTime, default=datetime.datetime.now)
    age = Column(db.Integer, default=0)
    telegram_id = Column(db.BIGINT, default=None)
    source_id = Column(db.Integer)
    avito_chat_id = Column(db.String(128), default=None)
    avito_user_id = Column(db.String(128), default=None)
    whatsapp_chat_id = Column(db.String(128), default=None)
    is_ban = Column(db.Boolean, default=False)
    tg_id = Column(db.BIGINT, default=None)
    source_code = Column(db.String(64), default=None)
    avito_type = Column(db.Integer, default=2)
    dialog_token = Column(db.String(64), default=None)

    def get_source(self):
        if self.source_id == 1:
            return 'Avito'
        elif self.source_id == 2:
            return 'WhatsApp'
        elif self.source_id == 3:
            return 'Telegram'
        elif self.source_id == 4:
            return 'стандарт-работа.рф'
        else:
            return 'Неизвестно'

    def get_status(self):
        if self.status == 0:
            return 'Начал анкетирование'
        elif self.status == 1:
            return 'Указал имя'
        elif self.status == 2:
            return 'Указал возраст'
        elif self.status == 3:
            return 'Указал телефон'
        elif self.status == 4:
            return 'Указал город'
        elif self.status == 5:
            return 'Подтвердил данные'
        elif self.status == 6:
            return 'Получил ссылку'
        elif self.status == 10:
            return 'В группе'
        elif self.status == 11:
            return 'Покинул группу'
        elif self.status == 15:
            return 'Ожидает добавление города'
        elif self.status == 16:
            return 'Ошибка создания ссылки'

    @staticmethod
    def get_status_by_id(status):
        if status == 0:
            return 'Начал анкетирование'
        elif status == 1:
            return 'Указал имя'
        elif status == 2:
            return 'Указал возраст'
        elif status == 3:
            return 'Указал телефон'
        elif status == 4:
            return 'Указал город'
        elif status == 5:
            return 'Подтвердил данные'
        elif status == 6:
            return 'Получил ссылку'
        elif status == 10:
            return 'В группе'
        elif status == 11:
            return 'Покинул группу'
        elif status == 15:
            return 'Ожидает добавление города'
        elif status == 16:
            return 'Ошибка создания ссылки'
        elif status == -71:
            return 'Звонок от Регины'

    @staticmethod
    def get_source_by_id(source_id):
        if source_id == 1:
            return 'Avito'
        elif source_id == 2:
            return 'WhatsApp'
        elif source_id == 3:
            return 'Telegram'
        elif source_id == 4:
            return 'стандарт-работа.рф'
        else:
            return 'Неизвестно'


class MemberEvent(Base):
    __tablename__ = 'member_events'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    date = Column(db.DateTime, default=datetime.datetime.now)
    event = Column(db.Text)
    member_id = Column(db.Integer)