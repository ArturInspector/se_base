from sqlalchemy import Column
from db import Base
import sqlalchemy as db
import datetime


class ChatLog(Base):
    __tablename__ = 'chats_logs'
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    webhook_id = Column(db.String(64))
    message_id = Column(db.String(64))
    chat_id = Column(db.String(64), index=True)  # Indexed for performance
    user_id = Column(db.Integer)
    author_id = Column(db.Integer)
    created_at = Column(db.DateTime, index=True)
    message = Column(db.Text)
    create_date = Column(db.DateTime, default=datetime.datetime.now)
    is_success = Column(db.Boolean, default=True)
    answer = Column(db.Text, default='')
    comment = Column(db.Text)
    
    # ═══════════════════════════════════════════════════════════
    # KPI FIELDS (NEW) - для оценки качества диалогов
    # ═══════════════════════════════════════════════════════════
    
    # Извлеченные данные (structured)
    extracted_city = Column(db.String(100))
    extracted_people = Column(db.Integer)
    extracted_hours = Column(db.Integer)
    extracted_phone = Column(db.String(20))
    extracted_intent = Column(db.String(50))  # price/booking/question/unclear
    
    # Действия AI
    ai_model = Column(db.String(50), default='gpt-4o')  # Какая модель использовалась
    function_calls = Column(db.Text)  # JSON: какие функции вызвал AI
    had_tool_calls = Column(db.Boolean, default=False)
    deal_created = Column(db.Boolean, default=False)  # Создана ли сделка
    deal_id = Column(db.Integer)  # ID сделки в Битриксе
    
    # Метрики качества (auto-graded)
    quality_score = Column(db.Float)  # 0.0-1.0: общая оценка качества
    has_hallucination = Column(db.Boolean, default=False)  # Галлюцинация
    is_too_verbose = Column(db.Boolean, default=False)  # Слишком длинный ответ
    missed_opportunity = Column(db.Boolean, default=False)  # Упустил возможность
    
    # Категория результата
    outcome = Column(db.String(50))  # success/failed/clarification/handoff
    failure_reason = Column(db.String(100))  # Причина неудачи
    
    # Для A/B testing
    experiment_variant = Column(db.String(50))  # 'control', 'fsm', 'structured_outputs', etc.
    
    # Метаданные для анализа
    response_time_ms = Column(db.Integer)  # Время ответа AI в мс
    tokens_used = Column(db.Integer)  # Токены потрачены


class ConversationGrade(Base):
    """
    Оценка целого диалога (не отдельного сообщения)
    Создается когда диалог завершен (сделка создана или клиент ушел)
    """
    __tablename__ = 'conversation_grades'
    
    id = Column(db.Integer, primary_key=True, autoincrement=True)
    chat_id = Column(db.String(64), unique=True, index=True)
    
    # Результат диалога
    outcome = Column(db.String(50))  # 'deal_created', 'client_left', 'handoff', 'rejected'
    deal_id = Column(db.Integer)
    
    # Метрики эффективности
    total_messages = Column(db.Integer)  # Всего сообщений в диалоге
    messages_to_deal = Column(db.Integer)  # Сколько понадобилось для сделки
    unnecessary_questions = Column(db.Integer)  # Лишние переспросы
    
    # Качественные метрики
    had_hallucinations = Column(db.Boolean, default=False)
    had_data_extraction_errors = Column(db.Boolean, default=False)
    had_business_rule_violations = Column(db.Boolean, default=False)
    
    # Оценка (0-100)
    conversation_score = Column(db.Float)  # Итоговая оценка диалога
    
    # Временные метрики
    started_at = Column(db.DateTime)
    completed_at = Column(db.DateTime)
    duration_minutes = Column(db.Float)
    
    # A/B testing
    experiment_variant = Column(db.String(50))
    
    # Дополнительный контекст
    notes = Column(db.Text)  # Автоматически сгенерированные заметки
    
    created_at = Column(db.DateTime, default=datetime.datetime.now)
