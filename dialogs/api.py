from typing import Union, List
from db import Session
from .entities import *
from uuid import uuid4
from .models import *
from errors import *
import messages


def get_dialog_by_id(dialog_id, session=None) -> Union[Dialog, None]:
    if session is None:
        with Session() as session:
            dialog = session.query(Dialog).get(dialog_id)
    else:
        dialog = session.query(Dialog).get(dialog_id)
    return dialog


def get_dialog_by_token(token, session=None) -> Union[Dialog, None]:
    if session is None:
        with Session() as session:
            dialog = session.query(Dialog).filter(Dialog.token == token).first()
    else:
        dialog = session.query(Dialog).filter(Dialog.token == token).first()
    return dialog


def get_dialogs(session=None) -> List[Dialog]:
    if session is None:
        with Session() as session:
            dialogs_list = session.query(Dialog).all()
    else:
        dialogs_list = session.query(Dialog).all()
    return dialogs_list


def create_dialog(model: CreateDialogModel) -> Dialog:
    with Session() as session:
        token = str(uuid4())
        dialog = Dialog(token=token, **model.model_dump())
        session.add(dialog)
        session.commit()
    dialog = get_dialog_by_token(token)
    messages.api.create_message(dialog_token=dialog.token, text='Начать анкетирование', is_system=False)
    return dialog