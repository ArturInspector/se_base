from db import Session
from .entities import *
from errors import *
import members


def get_short_by_id(short_id, session=None):
    if session is None:
        with Session() as session:
            short = session.query(Short).get(short_id)
    else:
        short = session.query(Short).get(short_id)
    return short


def get_short_by_link(link, session=None):
    if session is None:
        with Session() as session:
            short = session.query(Short).filter(Short.link == link).first()
    else:
        short = session.query(Short).filter(Short.link == link).first()
    return short


def get_shorts(is_all=False, session=None):
    if session is None:
        with Session() as session:
            if is_all:
                shorts_list = session.query(Short).all()
            else:
                shorts_list = session.query(Short).filter(Short.is_removed == False).all()
    else:
        if is_all:
            shorts_list = session.query(Short).all()
        else:
            shorts_list = session.query(Short).filter(Short.is_removed == False).all()
    return shorts_list


def create_short(name, link: str):
    link = str(link).lower()
    if len(link) < 1:
        raise IncorrectDataValue('Укажите ссылку')
    if len(name) < 1:
        raise IncorrectDataValue('Укажите название')

    with Session() as session:
        check = get_short_by_link(link, session)
        if check is not None:
            raise IncorrectDataValue('Такая ссылка уже существует')

        session.add(Short(name=name, link=link))
        session.commit()


def create_visit(link):
    with Session() as session:
        short = get_short_by_link(link, session)
        short_id = short.id if short is not None else 0
        session.add(Visit(short_id=short_id, link=link))
        session.commit()


def get_shorts_full():
    with Session() as session:
        shorts_list = get_shorts(session=session)
        visits_list = session.query(Visit).all()
        members_list = members.api.get_members(session)

    for short in shorts_list:
        short.visits = list(filter(lambda visit: visit.short_id == short.id, visits_list))
        short.members = list(filter(lambda member: member.source_code == short.link, members_list))
        short.invites = list(filter(lambda member: member.status == 10, short.members))
        short.leaves = list(filter(lambda member: member.status == 11, short.members))

        try:
            short.conversion = len(short.invites) / len(short.visits)
        except:
            short.conversion = 0
    return shorts_list
