from flask_socketio import emit
from typing import Union, List
from db import Session
from .entities import *
from errors import *
from uuid import uuid4
import dialogs
import traceback
import utils
import chat


def get_message_by_id(message_id, session=None) -> Union[Message, None]:
    if session is None:
        with Session() as session:
            message = session.query(Message).get(message_id)
    else:
        message = session.query(Message).get(message_id)
    return message


def get_message_by_token(token, session=None) -> Union[Message, None]:
    if session is None:
        with Session() as session:
            message = session.query(Message).filter(Message.token == token).first()
    else:
        message = session.query(Message).filter(Message.token == token).first()
    return message


def get_messages_by_dialog_id(dialog_id, session=None) -> List[Message]:
    if session is None:
        with Session() as session:
            messages_list = session.query(Message).filter(Message.dialog_id == dialog_id).all()
    else:
        messages_list = session.query(Message).filter(Message.dialog_id == dialog_id).all()
    return messages_list


def get_messages_by_dialog_token(dialog_token, session=None) -> List[Message]:
    if session is None:
        with Session() as session:
            messages_list = session.query(Message).filter(Message.dialog_token == dialog_token).all()
    else:
        messages_list = session.query(Message).filter(Message.dialog_token == dialog_token).all()
    return messages_list


def create_message(dialog_token: str, text: str, buttons: List[str] = [], is_system: bool = True) -> Message:
    if is_system is False and len(buttons) > 0:
        raise IncorrectDataValue('Кнопки доступны только для системных сообщений')
    if len(text) == 0:
        raise IncorrectDataValue('Укажите текст сообщения')

    with Session() as session:
        text = utils.wrap_links(text)
        dialog = dialogs.api.get_dialog_by_token(dialog_token, session=session)
        if dialog is None:
            raise IncorrectDataValue('Диалог не найден')

        token = str(uuid4())
        message = Message(dialog_id=dialog.id, dialog_token=dialog_token, is_system=is_system, text=text,
                          buttons=buttons, token=token)
        session.add(message)
        session.commit()

    message = get_message_by_token(token)

    try:
        emit('message', utils.to_json({'message': message}), room=message.dialog_token, namespace='/s/dialogs')
    except:
        print(traceback.format_exc())

    if message.is_system is False:
        chat.chat(4, message)

    return message