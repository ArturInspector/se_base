import datetime
from typing import Dict, List
import logging

from .config import MAX_DIALOGUE_CONTEXT_SIZE, DIALOGUE_CONTEXT_LIMIT

logger = logging.getLogger(__name__)


class DialogueContextManager:
    """
    Менеджер контекста диалога с поддержкой БД
    
    Теперь история берется из chats_log.api.get_chat_history()
    In-memory кэш используется только как fallback и для быстрого доступа
    """
    
    def __init__(self, use_db: bool = True):
        self.dialogue_context = {}
        self.use_db = use_db
    
    def add_message(self, chat_id: str, message: str, is_user: bool):
        """
        Добавление сообщения в in-memory кэш
        Реальное сохранение происходит через chats_log.api.create_chat_log()
        """
        if chat_id not in self.dialogue_context:
            self.dialogue_context[chat_id] = []
        
        self.dialogue_context[chat_id].append({
            'message': message,
            'is_user': is_user,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        logger.debug(f"Добавлено сообщение в контекст чата {chat_id}: is_user={is_user}")
        
        if len(self.dialogue_context) > MAX_DIALOGUE_CONTEXT_SIZE:
            logger.info(f"Очистка старых контекстов (размер: {len(self.dialogue_context)})")
            self.dialogue_context.clear()
    
    def get_context(self, chat_id: str, limit: int = DIALOGUE_CONTEXT_LIMIT) -> List[Dict]:
        """Получение контекста (для обратной совместимости)"""
        if chat_id not in self.dialogue_context:
            return []
        
        recent_messages = self.dialogue_context[chat_id][-limit:]
        logger.debug(f"Получен контекст для чата {chat_id}: {len(recent_messages)} сообщений")
        return recent_messages
    
    def get_openai_messages(self, chat_id: str, limit: int = DIALOGUE_CONTEXT_LIMIT) -> List[Dict[str, str]]:
        """
        Получение истории в формате OpenAI messages из БД или памяти
        
        Returns:
            [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."},
                ...
            ]
        """
        if self.use_db:
            try:
                import chats_log
                history = chats_log.api.get_chat_history(chat_id, limit=limit)
                if history:
                    logger.debug(f"Загружена история из БД: {len(history)} сообщений")
                    return history
                else:
                    logger.debug(f"История в БД пуста, используем in-memory")
            except Exception as e:
                logger.error(f"Ошибка загрузки истории из БД: {e}, используем in-memory")
        
        if chat_id not in self.dialogue_context:
            return []
        
        messages = self.dialogue_context[chat_id][-limit:]
        openai_messages = []
        for msg in messages:
            role = "user" if msg['is_user'] else "assistant"
            openai_messages.append({
                "role": role,
                "content": msg['message']
            })
        
        if openai_messages:
            logger.debug(f"Загружена история из памяти: {len(openai_messages)} сообщений")
        
        return openai_messages
    
    def get_formatted_context(self, chat_id: str, limit: int = DIALOGUE_CONTEXT_LIMIT) -> str:
        """Получение контекста в текстовом формате"""
        messages = self.get_openai_messages(chat_id, limit)
        if not messages:
            return "Нет предыдущих сообщений"
        
        formatted = "\n".join([
            f"{'Клиент' if msg['role'] == 'user' else 'Бот'}: {msg['content']}"
            for msg in messages
        ])
        return formatted
    
    def get_dialogue_summary(self, chat_id: str) -> str:
        """Получение краткого саммари для Битрикса"""
        if self.use_db:
            try:
                import chats_log
                return chats_log.api.get_chat_summary(chat_id, max_messages=5)
            except Exception as e:
                logger.error(f"Ошибка получения саммари из БД: {e}")
        
        messages = self.get_context(chat_id)
        if not messages:
            return "Нет истории диалога"
        
        user_messages = [msg['message'] for msg in messages if msg['is_user']]
        return " | ".join(user_messages[:3])
    
    def clear_old_contexts(self):
        """Очистка in-memory кэша"""
        self.dialogue_context.clear()
        logger.info("Все контексты очищены")

