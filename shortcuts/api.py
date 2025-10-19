from typing import Union, List
from db import Session
from errors import *
from .entities import *
from members.entities import Member
import utils
import datetime
import whatsapp


def get_message_by_id(message_id, session=None) -> Union[Message, None]:
    if session is None:
        with Session() as session:
            message = session.query(Message).get(message_id)
    else:
        message = session.query(Message).get(message_id)
    return message


def get_messages(phone=None, is_send=None, session=None) -> List[Message]:
    if session is None:
        with Session() as session:
            messages_list = session.query(Message)

            if phone is not None:
                messages_list = messages_list.filter(Message.phone == phone)
            if is_send is not None:
                messages_list = messages_list.filter(Message.is_send == is_send)
    else:
        messages_list = session.query(Message)

        if phone is not None:
            messages_list = messages_list.filter(Message.phone == phone)
        if is_send is not None:
            messages_list = messages_list.filter(Message.is_send == is_send)

    messages_list = messages_list.all()
    messages_list.sort(key=lambda message: message.id, reverse=True)

    return messages_list


def get_message_by_phone(phone):
    with Session() as session:
        message = session.query(Message).filter(Message.phone == phone, Message.is_business.is_(True)).first()
    return message


def create_message(phone, message, is_business=False):
    if len(message) == 0:
        raise IncorrectDataValue('Укажите текст сообщения')

    phone = utils.telephone(phone)

    if phone is None:
        raise IncorrectDataValue('Укажите корректный номер телефона')

    try:
        whatsapp.api.send_message(phone, text=message, is_business=is_business)
    except:
        raise IncorrectDataValue('Ошибка отправки сообщения')

    with Session() as session:
        message = Message(phone=phone, message=message, is_business=is_business, is_send=True, finish_date=datetime.datetime.now())
        session.add(message)
        session.commit()


def remove_message(message_id):
    with Session() as session:
        message = get_message_by_id(message_id, session=session)
        if message is not None:
            session.delete(message)
            session.commit()


def get_tasks(session=None) -> List[TaskNotify]:
    if session is None:
        with Session() as session:
            tasks_list = session.query(TaskNotify).all()
    else:
        tasks_list = session.query(TaskNotify).all()
    return tasks_list


def create_task_notify(member_status, minutes, message):
    with Session() as session:
        if Member.get_status_by_id(member_status) is None:
            raise IncorrectDataValue('Укажите корректный статус')

        if minutes < 1:
            raise IncorrectDataValue('Кол-во минут не может быть меньше 1')

        if len(message) == 0:
            raise IncorrectDataValue('Укажите сообщение')

        task = TaskNotify(member_status=member_status, minutes=minutes, message=message)
        session.add(task)
        session.commit()


def remove_task_notify(notify_id):
    with Session() as session:
        task = session.query(TaskNotify).get(notify_id)

        if task is not None:
            session.delete(task)
            session.commit()