from sqlalchemy import create_engine, event, exc
from sqlalchemy.pool import Pool
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import config

engine = create_engine(config.Production.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True, pool_size=8, max_overflow=4)

Session = sessionmaker(bind=engine)

Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)