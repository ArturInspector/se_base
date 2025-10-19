from db import Session
from .entities import *
from errors import *
from chat.models import AvitoMessageModel
import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def create_chat_log(model: AvitoMessageModel, is_success, answer='', comment='', session=None):
    if session is None:
        with Session() as session:
            webhook_id = model.id
            message_id = model.payload.value.id
            chat_id = model.payload.value.chat_id
            user_id = model.payload.value.user_id
            author_id = model.payload.value.author_id
            created_at = datetime.datetime.fromtimestamp(model.payload.value.created)
            message = model.payload.value.content.text

            chat_log = ChatLog(webhook_id=webhook_id, message_id=message_id, chat_id=chat_id, user_id=user_id,
                               author_id=author_id, created_at=created_at, message=message, is_success=is_success,
                               answer=answer, comment=comment)
            session.add(chat_log)
            session.commit()
    else:
        webhook_id = model.id
        message_id = model.payload.value.id
        chat_id = model.payload.value.chat_id
        user_id = model.payload.value.user_id
        author_id = model.payload.value.author_id
        created_at = datetime.datetime.fromtimestamp(model.payload.value.created)
        message = model.payload.value.content.text

        chat_log = ChatLog(webhook_id=webhook_id, message_id=message_id, chat_id=chat_id, user_id=user_id,
                           author_id=author_id, created_at=created_at, message=message, is_success=is_success,
                           answer=answer, comment=comment)
        session.add(chat_log)


def get_chat_history(chat_id: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    Получение истории диалога из БД в формате OpenAI messages
    
    Args:
        chat_id: ID чата
        limit: Максимальное количество пар сообщений (user+assistant)
    
    Returns:
        Список сообщений в формате OpenAI:
        [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."},
            ...
        ]
    """
    with Session() as session:
        logs = session.query(ChatLog).filter(
            ChatLog.chat_id == chat_id,
            ChatLog.is_success == True
        ).order_by(
            ChatLog.created_at.desc()
        ).limit(limit).all()
        
        messages = []
        for log in reversed(logs):
            if log.message:
                messages.append({
                    "role": "user",
                    "content": log.message
                })
            
            if log.answer and log.answer != 'None' and log.answer != '':
                messages.append({
                    "role": "assistant",
                    "content": log.answer
                })
        
        logger.debug(f"Загружена история чата {chat_id}: {len(messages)} сообщений")
        return messages


def get_chat_summary(chat_id: str, max_messages: int = 5) -> str:
    """
    Получение краткого саммари диалога для Битрикса
    
    Args:
        chat_id: ID чата
        max_messages: Максимальное количество сообщений
    
    Returns:
        Строка с последними сообщениями пользователя
    """
    with Session() as session:
        logs = session.query(ChatLog).filter(
            ChatLog.chat_id == chat_id
        ).order_by(
            ChatLog.created_at.desc()
        ).limit(max_messages).all()
        
        user_messages = [log.message for log in reversed(logs) if log.message]
        return " | ".join(user_messages)
