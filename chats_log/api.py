from db import Session
from .entities import *
from errors import *
from chat.models import AvitoMessageModel
import datetime
from typing import List, Dict, Optional
import logging
import json

logger = logging.getLogger(__name__)


def create_chat_log(
    model: AvitoMessageModel, 
    is_success, 
    answer='', 
    comment='',
    extracted_data: Optional[Dict] = None,
    function_calls: Optional[List] = None,
    quality_score: Optional[float] = None,
    experiment_variant: Optional[str] = None,
    deal_created: bool = False,
    deal_id: Optional[int] = None,
    response_time_ms: Optional[int] = None,
    session=None
):
    
    webhook_id = model.id
    message_id = model.payload.value.id
    chat_id = model.payload.value.chat_id
    user_id = model.payload.value.user_id
    author_id = model.payload.value.author_id
    created_at = datetime.datetime.fromtimestamp(model.payload.value.created)
    message = model.payload.value.content.text
    
    extracted_city = extracted_data.get('city') if extracted_data else None
    extracted_people = extracted_data.get('people') if extracted_data else None
    extracted_hours = extracted_data.get('hours') if extracted_data else None
    extracted_phone = extracted_data.get('phone') if extracted_data else None
    extracted_intent = extracted_data.get('intent') if extracted_data else None
    
    had_tool_calls = bool(function_calls)
    function_calls_json = json.dumps(function_calls) if function_calls else None
    
    chat_log = ChatLog(
        webhook_id=webhook_id,
        message_id=message_id,
        chat_id=chat_id,
        user_id=user_id,
        author_id=author_id,
        created_at=created_at,
        message=message,
        is_success=is_success,
        answer=answer,
        comment=comment,
        extracted_city=extracted_city,
        extracted_people=extracted_people,
        extracted_hours=extracted_hours,
        extracted_phone=extracted_phone,
        extracted_intent=extracted_intent,
        function_calls=function_calls_json,
        had_tool_calls=had_tool_calls,
        deal_created=deal_created,
        deal_id=deal_id,
        quality_score=quality_score,
        experiment_variant=experiment_variant,
        response_time_ms=response_time_ms
    )
    
    if session is None:
        with Session() as session:
            session.add(chat_log)
            session.commit()
    else:
        session.add(chat_log)


def get_chat_history(chat_id: str, limit: int = 10) -> List[Dict[str, str]]:
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
    with Session() as session:
        logs = session.query(ChatLog).filter(
            ChatLog.chat_id == chat_id
        ).order_by(
            ChatLog.created_at.desc()
        ).limit(max_messages).all()
        
        user_messages = [log.message for log in reversed(logs) if log.message]
        return " | ".join(user_messages)


def save_conversation_grade(
    chat_id: str,
    outcome: str,
    deal_id: Optional[int],
    total_messages: int,
    messages_to_deal: Optional[int],
    conversation_score: float,
    had_hallucinations: bool,
    had_data_extraction_errors: bool,
    had_business_rule_violations: bool,
    experiment_variant: Optional[str],
    notes: Optional[str] = None
):
    with Session() as session:
        existing = session.query(ConversationGrade).filter(
            ConversationGrade.chat_id == chat_id
        ).first()
        
        if existing:
            existing.outcome = outcome
            existing.deal_id = deal_id
            existing.total_messages = total_messages
            existing.messages_to_deal = messages_to_deal
            existing.conversation_score = conversation_score
            existing.had_hallucinations = had_hallucinations
            existing.had_data_extraction_errors = had_data_extraction_errors
            existing.had_business_rule_violations = had_business_rule_violations
            existing.completed_at = datetime.datetime.now()
            if notes:
                existing.notes = notes
        else:
            grade = ConversationGrade(
                chat_id=chat_id,
                outcome=outcome,
                deal_id=deal_id,
                total_messages=total_messages,
                messages_to_deal=messages_to_deal,
                conversation_score=conversation_score,
                had_hallucinations=had_hallucinations,
                had_data_extraction_errors=had_data_extraction_errors,
                had_business_rule_violations=had_business_rule_violations,
                experiment_variant=experiment_variant,
                notes=notes,
                started_at=datetime.datetime.now(),
                completed_at=datetime.datetime.now()
            )
            session.add(grade)
        
        session.commit()
