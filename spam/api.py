from telebot.types import Message
from db import Session
from typing import Union, List
from .entities import *
from errors import *


def get_block_by_id(block_id, session=None) -> Union[SpamBlock, None]:
    if session is None:
        with Session() as session:
            block = session.query(SpamBlock).get(block_id)
    else:
        block = session.query(SpamBlock).get(block_id)
    return block


def get_blocks(session=None) -> List[SpamBlock]:
    if session is None:
        with Session() as session:
            blocks_list = session.query(SpamBlock).all()
    else:
        blocks_list = session.query(SpamBlock).all()
    return blocks_list


def create_block(message: Message, words_list: List[str], is_success: bool, error=None):
    with Session() as session:
        spam_block = SpamBlock(
            tg_id=message.from_user.id,
            tg_username=message.from_user.username,
            tg_first_name=message.from_user.first_name,
            tg_last_name=message.from_user.last_name,
            tg_group_id=message.chat.id,
            tg_group_name=message.chat.title,
            message=message.text,
            words_list=words_list,
            is_success=is_success,
            error=error
        )
        session.add(spam_block)
        session.commit()