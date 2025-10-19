from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class Dialog(Base):
    __tablename__ = 'dialogs'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    token = Column(db.String(64))
    create_date = Column(db.DateTime, default=datetime.datetime.now)
    source_id = Column(db.Integer, default=None)
    source_ident = Column(db.String(128), default=None)
    utm_source = Column(db.String(256), default=None)
    utm_medium = Column(db.String(256), default=None)
    utm_campaign = Column(db.String(256), default=None)
    utm_content = Column(db.String(256), default=None)
    utm_term = Column(db.String(256), default=None)