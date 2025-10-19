from telebot.types import Message as TGMessage
from .entities import *
from db import Session
from .models import *
from errors import *
import requests
import cities
import utils


def get_message_by_id(msg_id, session=None):
    if session is None:
        with Session() as session:
            message = session.query(Message).get(msg_id)
    else:
        message = session.query(Message).get(msg_id)
    return message


def get_messages_by_tg_id(tg_id, session=None):
    if session is None:
        with Session() as session:
            messages_list = session.query(Message).filter(Message.tg_id == tg_id).all()
    else:
        messages_list = session.query(Message).filter(Message.tg_id == tg_id).all()
    return messages_list


def get_messages(session=None):
    if session is None:
        with Session() as session:
            messages_list = session.query(Message).all()
    else:
        messages_list = session.query(Message).all()
    return messages_list


def create_message(message: TGMessage):
    city = cities.api.get_city_bt_group_id(message.chat.id)
    if city is None:
        return

    try:
        url = 'http://45.147.178.126:40001/kek/limits/processing'

        model = MessageModel(
            text=message.text,
            date=message.date,
            chat_name=message.chat.title,
            chat_id=message.chat.id,
            fias_id=city.fias,
        )

        requests.post(url, json=model.model_dump())
    except:
        pass

    username = ''
    if message.from_user.first_name is not None and message.from_user.last_name:
        username = '{} {}'.format(message.from_user.first_name, message.from_user.last_name)
    elif message.from_user.first_name is not None:
        username = message.from_user.first_name
    elif message.from_user.last_name is not None:
        username = message.from_user.last_name

    with Session() as session:
        message = Message(tg_id=message.from_user.id, tg_username=username, city_id=city.id,
                          message=message.text)
        session.add(message)
        session.commit()
    return


def get_admins(min_date=None, max_date=None):
    admins_list = {}
    messages_list = get_messages()

    if min_date is not None:
        messages_list = list(filter(lambda message: message.date >= min_date, messages_list))
    if max_date is not None:
        messages_list = list(filter(lambda message: message.date <= max_date, messages_list))

    for message in messages_list:
        if message.tg_id not in admins_list:
            admins_list[message.tg_id] = TGAdmin(message)
        else:
            admins_list[message.tg_id].messages.append(message)
    return [item[1] for item in list(admins_list.items())]


def get_admin(tg_id, min_date=None, max_date=None):
    messages_list = get_messages_by_tg_id(tg_id)

    if min_date is not None:
        messages_list = list(filter(lambda message: message.date >= min_date, messages_list))
    if max_date is not None:
        messages_list = list(filter(lambda message: message.date <= max_date, messages_list))

    cities_list = cities.api.get_cities()

    tg_admin = None
    for message in messages_list:
        message.city = utils.get_entity_by_id(message.city_id, cities_list)
        if tg_admin is None:
            tg_admin = TGAdmin(message)
        else:
            tg_admin.messages.append(message)

    tg_admin.messages.sort(key=lambda m: m.date, reverse=True)
    return tg_admin