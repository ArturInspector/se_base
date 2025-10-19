from db import Session
from .entities import *
from errors import *
# import bot  # Временно отключено
import members
import utils
import cities
import requests
import traceback


def get_selfemployer_code(ad_id, model):
    try:
        url = 'http://45.147.178.126:40001/kek/invites/create'

        data = {
            'ad_id': ad_id,
            'model': model
        }

        response = requests.post(url, json=data)
        return response.json()['code']
    except:
        print(traceback.format_exc())
        return None


def get_link_by_id(link_id, session=None):
    if session is None:
        with Session() as session:
            link = session.query(Link).get(link_id)
    else:
        link = session.query(Link).get(link_id)
    return link


def get_link_by_code(code, session=None):
    if session is None:
        with Session() as session:
            link = session.query(Link).filter(Link.code == code).first()
    else:
        link = session.query(Link).filter(Link.code == code).first()
    return link


def get_link_by_link(link, session=None):
    if session is None:
        with Session() as session:
            link = session.query(Link).filter(Link.link == link).first()
    else:
        link = session.query(Link).filter(Link.link == link).first()
    return link


def get_links_by_member_id(member_id, session=None):
    if session is None:
        with Session() as session:
            links_list = session.query(Link).filter(Link.member_id == member_id).all()
    else:
        links_list = session.query(Link).filter(Link.member_id == member_id).all()
    return links_list


def create_link(member_id):
    with Session() as session:
        member = members.api.get_member_by_id(member_id, session)
        link_name = 'member_{}'.format(member.id)
        try:
            # link = bot.create_invite_link(member.city_id, link_name)
            link = None  # Временно отключено
        except GroupNotAllowed:
            city = cities.api.get_city_by_id(member.city_id, session)
            member.status = 15
            member.last_update = datetime.datetime.now()
            session.commit()
            # bot.send_message('Не удалось добавить пользователя, так как бот не добавлен в группу города'
            #                  '\n\nID Пользователя:\n{}\n\nГород:\n{}\n\nДобавьте бота в группу города!'.format(
            #     member.id, city.name
            # ))
            raise GroupNotAllowed()
        except Exception as e:
            bot.send_message('Не удалось создать пригласительную ссылку\n\nПользователь:\n[{}] {}\n\nГород ID:\n{}'
                             '\n\nОшибка:\n{}'.format(member.id, member.phone, member.city_id, str(e)))
            member.status = 16
            member.last_update = datetime.datetime.now()
            session.commit()
            raise IncorrectDataValue(message='')

        code = utils.get_random_string(8)
        check = get_link_by_code(code, session)
        if check is not None:
            while check is not None:
                code = utils.get_random_string(8)
                check = get_link_by_code(code, session)

        link = Link(code=code, member_id=member.id, link=link, city_id=member.city_id)
        session.add(link)
        member.status = 6
        member.last_update = datetime.datetime.now()
        members.api.create_event(member.id, 'Пользователю выдана ссылка {}'.format(link.link), session)
        session.commit()
    return get_link_by_code(code)


def create_member_link(member, session):
    link_name = 'member_{}'.format(member.id)
    try:
        link = bot.create_invite_link(member.city_id, link_name)
    except GroupNotAllowed:
        city = cities.api.get_city_by_id(member.city_id, session)
        member.status = 15
        member.last_update = datetime.datetime.now()
        bot.send_message('Не удалось добавить пользователя, так как бот не добавлен в группу города'
                         '\n\nID Пользователя:\n{}\n\nГород:\n{}\n\nДобавьте бота в группу города!'.format(
            member.id, city.name
        ))
        raise GroupNotAllowed()
    except Exception as e:
        bot.send_message('Не удалось создать пригласительную ссылку\n\nПользователь:\n[{}] {}\n\nГород ID:\n{}'
                         '\n\nОшибка:\n{}'.format(member.id, member.phone, member.city_id, str(e)))
        member.status = 16
        member.last_update = datetime.datetime.now()
        raise IncorrectDataValue(message='')

    code = utils.get_random_string(8)
    check = get_link_by_code(code, session)
    if check is not None:
        while check is not None:
            code = utils.get_random_string(8)
            check = get_link_by_code(code, session)

    link = Link(code=code, member_id=member.id, link=link, city_id=member.city_id)
    session.add(link)
    member.status = 6
    member.last_update = datetime.datetime.now()
    members.api.create_event(member.id, 'Пользователю выдана ссылка {}'.format(link.link), session)
    return link


def create_moscow_link(member_id):
    with Session() as session:
        member = members.api.get_member_by_id(member_id, session)
        link_name = 'member_{}'.format(member.id)
        try:
            link = bot.create_invite_link(510, link_name)
        except GroupNotAllowed:
            return None
        except Exception as e:
            bot.send_message('Не удалось создать пригласительную ссылку\n\nПользователь:\n[{}] {}\n\nГород ID:\n{}'
                             '\n\nОшибка:\n{}'.format(member.id, member.phone, member.city_id, str(e)))
            return None

        code = utils.get_random_string(8)
        check = get_link_by_code(code, session)
        if check is not None:
            while check is not None:
                code = utils.get_random_string(8)
                check = get_link_by_code(code, session)

        link = Link(code=code, member_id=member.id, link=link, city_id=member.city_id)
        session.add(link)
        members.api.create_event(member.id, 'Пользователю выдана ссылка {}'.format(link.link), session)
        session.commit()
    return get_link_by_code(code)


def create_spb_link(member_id):
    with Session() as session:
        member = members.api.get_member_by_id(member_id, session)
        link_name = 'member_{}'.format(member.id)
        try:
            link = bot.create_invite_link(787, link_name)
        except GroupNotAllowed:
            return None
        except Exception as e:
            bot.send_message('Не удалось создать пригласительную ссылку\n\nПользователь:\n[{}] {}\n\nГород ID:\n{}'
                             '\n\nОшибка:\n{}'.format(member.id, member.phone, member.city_id, str(e)))
            return None

        code = utils.get_random_string(8)
        check = get_link_by_code(code, session)
        if check is not None:
            while check is not None:
                code = utils.get_random_string(8)
                check = get_link_by_code(code, session)

        link = Link(code=code, member_id=member.id, link=link, city_id=member.city_id)
        session.add(link)
        members.api.create_event(member.id, 'Пользователю выдана ссылка {}'.format(link.link), session)
        session.commit()
    return get_link_by_code(code)


def create_link_by_kladr_id(kladr_id):
    city = cities.api.get_city_by_kladr(kladr_id)
    try:
        link = bot.create_invite_link(city.id, '')
    except GroupNotAllowed:
        return None
    except Exception as e:
        bot.send_message('Не удалось создать пригласительную ссылку\n\nГород ID:\n{}'
                         '\n\nОшибка:\n{}'.format(city_id, str(e)))
        return None
    return link


def in_group(link_str, tg_id):
    with Session() as session:
        link = get_link_by_link(link_str, session)
        if link is None:
            return

        member = members.api.get_member_by_id(link.member_id, session)
        member.telegram_id = tg_id
        member.status = 10
        link.status = 10
        session.commit()


def set_in_group(tg_id, chat_id, is_in: bool):
    city = cities.api.get_city_by_group_id(chat_id)
    if city is None:
        return

    url = 'http://45.147.178.126:40001/d/in_group'

    params = {
        'tg_id': tg_id,
        'kladr_id': city.kladr,
        'is_in': 1 if is_in else False
    }

    requests.get(url, params)