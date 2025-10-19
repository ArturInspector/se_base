from pydantic import BaseModel
from typing import Literal, Optional, Union


class KazanModel(BaseModel):
    first_message: str = """Здравствуйте!

Мы предоставляем разовую подработку 
и постоянную работу с ежедневными выплатами.
"""
    second_message: str = """Актуальные заказы отправляются в телеграм. 
Чтобы получить первый заказ уже сегодня 
перейдите по ссылке ниже:"""

    third_message: str = """https://t.me/se_register_test_bot"""


class AvitoMessageContent(BaseModel):
    text: str


class AvitoMessageValue(BaseModel):
    id: str
    chat_id: str
    user_id: int
    author_id: int
    created: int
    type: Literal['text', 'system', 'link']
    chat_type: Literal['u2i']
    item_id: Union[None, int] = None
    content: AvitoMessageContent


class AvitoMessagePayload(BaseModel):
    type: Literal['message']
    value: AvitoMessageValue


class AvitoMessageModel(BaseModel):
    id: str
    version: str
    timestamp: int
    payload: AvitoMessagePayload