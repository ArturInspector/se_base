"""
Логика переходов между состояниями FSM

SRP: Только определение правил переходов
OCP: Легко добавить новые правила
"""
import re
import logging
from typing import Optional, Dict, Tuple

from .states import DialogueState, StateContext

logger = logging.getLogger(__name__)


class TransitionValidator:
    """
    Валидация и проверка условий для переходов
    
    SRP: Только проверки, не решения
    """
    
    @staticmethod
    def extract_phone(message: str) -> Optional[str]:
        """Извлечь телефон из сообщения"""
        try:
            import utils
            return utils.telephone(message)
        except Exception:
            # Fallback regex
            pattern = r'(\+7|8)?[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}'
            match = re.search(pattern, message)
            return match.group(0) if match else None
    
    @staticmethod
    def has_greeting_keywords(message: str) -> bool:
        """Проверка на приветствие"""
        greetings = ['привет', 'здравствуй', 'добрый', 'доброе', 'здрасте', 'здорово']
        msg_lower = message.lower()
        return any(word in msg_lower for word in greetings)
    
    @staticmethod
    def is_legal_entity_keywords(message: str) -> bool:
        """Признаки юридического лица"""
        keywords = [
            'офис', 'компания', 'юр.лицо', 'юрлицо', 'юридическое лицо',
            'организация', 'предприятие', 'счет', 'счёт', 'договор',
            'тех.задание', 'техническое задание', 'тз', 'инн', 'огрн',
            'для компании', 'для офиса', 'для организации'
        ]
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in keywords)
    
    @staticmethod
    def is_takelage_keywords(message: str) -> bool:
        """Признаки такелажа (тяжелые предметы)"""
        keywords = [
            'сейф', 'банкомат', 'пианино', 'рояль', 'станок',
            'более 100', '>100', 'больше 100', 'тяжел', 'такелаж'
        ]
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in keywords)
    
    @staticmethod
    def is_out_of_city_keywords(message: str) -> bool:
        """Признаки выезда за город"""
        keywords = [
            'за город', 'за пределы', 'снт', 'садовое товарищество',
            'дачный поселок', 'деревня', 'село', 'км от города'
        ]
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in keywords)
    
    @staticmethod
    def is_price_question(message: str) -> bool:
        """Клиент спрашивает про цену"""
        keywords = ['цена', 'сколько', 'стоимость', 'стоит', 'расчет', 'рассчитать']
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in keywords)
    
    @staticmethod
    def is_booking_intent(message: str) -> bool:
        """Клиент хочет заказать"""
        keywords = [
            'заказ', 'нужны', 'нужен', 'требуются', 'оформить',
            'записаться', 'хочу заказать', 'надо'
        ]
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in keywords)
    
    @staticmethod
    def is_positive_response(message: str) -> bool:
        """Положительный ответ (да, согласен, подходит)"""
        keywords = ['да', 'ага', 'угу', 'согласен', 'подходит', 'хорошо', 'окей', 'ок']
        msg_lower = message.lower().strip()
        return msg_lower in keywords or any(kw in msg_lower for kw in keywords)
    
    @staticmethod
    def is_negative_response(message: str) -> bool:
        """Отрицательный ответ (нет, дорого, не подходит)"""
        keywords = ['нет', 'не подходит', 'дорого', 'не устраивает', 'много']
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in keywords)


class TransitionEngine:
    """
    Движок переходов между состояниями
    
    SRP: Определяет следующее состояние на основе текущего + данных
    """
    
    def __init__(self):
        self.validator = TransitionValidator()
        logger.info("[FSM] TransitionEngine инициализирован")
    
    def determine_next_state(
        self,
        context: StateContext,
        user_message: str,
        ai_extracted_data: Dict
    ) -> Tuple[DialogueState, str]:
        """
        Определить следующее состояние
        
        Args:
            context: Текущий контекст диалога
            user_message: Сообщение от клиента
            ai_extracted_data: Данные извлеченные AI (city, hours, people и т.д.)
            
        Returns:
            (новое_состояние, причина_перехода)
        """
        current = context.current_state
        logger.debug(f"[FSM] Определение перехода из {current}")
        
        # Обновляем контекст извлеченными данными
        self._update_context_from_ai(context, ai_extracted_data)
        
        # Проверка специальных флагов
        if self.validator.is_legal_entity_keywords(user_message):
            context.is_legal_entity = True
        
        if self.validator.is_takelage_keywords(user_message):
            context.is_takelage = True
            context.requires_personal_calc = True
        
        if self.validator.is_out_of_city_keywords(user_message):
            context.is_out_of_city = True
            context.requires_personal_calc = True
        
        # ПРИОРИТЕТ 1: Телефон → всегда ведет к BOOKING_CONFIRMATION
        phone = self.validator.extract_phone(user_message)
        if phone:
            context.phone = phone
            logger.info(f"[FSM] Телефон получен: {phone}")
            return DialogueState.BOOKING_CONFIRMATION, "phone_provided"
        
        # ПРИОРИТЕТ 2: Персональный расчет → HANDOFF
        if context.requires_personal_calc and not context.phone:
            return DialogueState.HANDOFF_OPERATOR, "requires_personal_calculation"
        
        # ПРИОРИТЕТ 3: Маршрутизация по текущему состоянию
        if current == DialogueState.GREETING:
            return self._from_greeting(context, user_message)
        
        elif current == DialogueState.INTENT_CLASSIFICATION:
            return self._from_intent_classification(context, user_message)
        
        elif current == DialogueState.CITY_INQUIRY:
            return self._from_city_inquiry(context, user_message)
        
        elif current == DialogueState.PRICE_INQUIRY:
            return self._from_price_inquiry(context, user_message)
        
        elif current == DialogueState.BOOKING_COLLECTION:
            return self._from_booking_collection(context, user_message)
        
        elif current == DialogueState.BOOKING_CONFIRMATION:
            return self._from_booking_confirmation(context, user_message)
        
        elif current == DialogueState.ISSUE_RESOLUTION:
            return self._from_issue_resolution(context, user_message)
        
        elif current == DialogueState.HANDOFF_OPERATOR:
            return self._from_handoff(context, user_message)
        
        else:
            logger.warning(f"[FSM] Неизвестное состояние {current}, fallback to GREETING")
            return DialogueState.GREETING, "unknown_state_fallback"
    
    def _from_greeting(self, ctx: StateContext, msg: str) -> Tuple[DialogueState, str]:
        """Переход из GREETING"""
        
        # Юрлицо или специальный случай → handoff
        if ctx.is_legal_entity or ctx.requires_personal_calc:
            return DialogueState.HANDOFF_OPERATOR, "special_case_detected"
        
        # Есть город?
        if ctx.city:
            # Есть минимум данных → можем считать цену
            if ctx.has_minimum_data():
                return DialogueState.PRICE_INQUIRY, "has_city_and_people"
            # Только город → собираем детали
            return DialogueState.BOOKING_COLLECTION, "has_city_need_details"
        else:
            # Нет города → спросить
            return DialogueState.CITY_INQUIRY, "city_unknown"
    
    def _from_intent_classification(self, ctx: StateContext, msg: str) -> Tuple[DialogueState, str]:
        """Переход из INTENT_CLASSIFICATION"""
        
        # Проверяем нужно ли уточнить юрлицо
        if ctx.needs_legal_clarification:
            if 'компан' in msg.lower() or 'организац' in msg.lower() or 'офис' in msg.lower():
                ctx.is_legal_entity = True
                ctx.needs_legal_clarification = False
                return DialogueState.HANDOFF_OPERATOR, "confirmed_legal_entity"
            elif 'частн' in msg.lower() or 'себя' in msg.lower() or 'лично' in msg.lower():
                ctx.is_legal_entity = False
                ctx.needs_legal_clarification = False
                # Продолжаем обычный флоу
                if ctx.has_minimum_data():
                    return DialogueState.PRICE_INQUIRY, "confirmed_private_can_calculate"
                return DialogueState.BOOKING_COLLECTION, "confirmed_private_continue"
        
        # Определяем намерение
        if self.validator.is_price_question(msg):
            ctx.intent = "price"
            if ctx.city:
                return DialogueState.PRICE_INQUIRY, "intent_price_with_city"
            else:
                return DialogueState.CITY_INQUIRY, "intent_price_need_city"
        
        elif self.validator.is_booking_intent(msg):
            ctx.intent = "booking"
            if ctx.city:
                return DialogueState.BOOKING_COLLECTION, "intent_booking_with_city"
            else:
                return DialogueState.CITY_INQUIRY, "intent_booking_need_city"
        
        else:
            return DialogueState.ISSUE_RESOLUTION, "unclear_intent"
    
    def _from_city_inquiry(self, ctx: StateContext, msg: str) -> Tuple[DialogueState, str]:
        """Переход из CITY_INQUIRY"""
        
        if ctx.city:
            # Город получен
            ctx.reset_retry_counters()
            
            # Что дальше?
            if ctx.intent == "price" and ctx.has_minimum_data():
                return DialogueState.PRICE_INQUIRY, "city_received_can_calculate"
            else:
                return DialogueState.BOOKING_COLLECTION, "city_received_collect_details"
        else:
            # Город не определен
            ctx.retry_count += 1
            if ctx.retry_count >= 3:
                return DialogueState.HANDOFF_OPERATOR, "city_retry_exceeded"
            return DialogueState.CITY_INQUIRY, "city_still_unknown"
    
    def _from_price_inquiry(self, ctx: StateContext, msg: str) -> Tuple[DialogueState, str]:
        """Переход из PRICE_INQUIRY"""
        
        # Клиент готов заказать?
        if self.validator.is_positive_response(msg) or 'заказ' in msg.lower():
            return DialogueState.BOOKING_COLLECTION, "client_ready_to_book"
        
        # Клиент не согласен?
        if self.validator.is_negative_response(msg):
            return DialogueState.ISSUE_RESOLUTION, "client_objection"
        
        # Дополнительные вопросы по цене
        return DialogueState.PRICE_INQUIRY, "additional_price_questions"
    
    def _from_booking_collection(self, ctx: StateContext, msg: str) -> Tuple[DialogueState, str]:
        """Переход из BOOKING_COLLECTION"""
        
        # КРИТИЧЕСКАЯ ПРОВЕРКА: 1 грузчик → отклонить
        if ctx.people and ctx.people == 1:
            logger.warning("[FSM] Клиент просит 1 грузчика - отклоняем")
            return DialogueState.ISSUE_RESOLUTION, "one_person_requested"
        
        # Проверяем нужно ли уточнить юрлицо
        if ctx.should_ask_legal_status() and not ctx.needs_legal_clarification:
            ctx.needs_legal_clarification = True
            return DialogueState.INTENT_CLASSIFICATION, "need_legal_clarification"
        
        # Все данные собраны?
        if ctx.has_complete_booking_data():
            return DialogueState.BOOKING_CONFIRMATION, "all_data_collected"
        
        # Продолжаем сбор
        return DialogueState.BOOKING_COLLECTION, "collecting_more_data"
    
    def _from_booking_confirmation(self, ctx: StateContext, msg: str) -> Tuple[DialogueState, str]:
        """Переход из BOOKING_CONFIRMATION"""
        # После создания сделки → завершение
        return DialogueState.COMPLETED, "deal_created"
    
    def _from_issue_resolution(self, ctx: StateContext, msg: str) -> Tuple[DialogueState, str]:
        """Переход из ISSUE_RESOLUTION"""
        
        # Проблема решена?
        if self.validator.is_positive_response(msg) or 'понятно' in msg.lower() or 'спасибо' in msg.lower():
            ctx.reset_retry_counters()
            if ctx.city:
                return DialogueState.BOOKING_COLLECTION, "issue_resolved_continue"
            else:
                return DialogueState.CITY_INQUIRY, "issue_resolved_need_city"
        
        # Проблема не решена
        ctx.fallback_count += 1
        if ctx.fallback_count >= 2:
            return DialogueState.HANDOFF_OPERATOR, "unresolved_issue"
        
        return DialogueState.ISSUE_RESOLUTION, "still_resolving"
    
    def _from_handoff(self, ctx: StateContext, msg: str) -> Tuple[DialogueState, str]:
        """Переход из HANDOFF_OPERATOR"""
        # После handoff обычно ждем телефон или завершаем
        return DialogueState.HANDOFF_OPERATOR, "waiting_for_phone_in_handoff"
    
    def _update_context_from_ai(self, ctx: StateContext, ai_data: Dict):
        """Обновить контекст данными от AI"""
        if 'city' in ai_data and ai_data['city']:
            old_city = ctx.city
            ctx.city = ai_data['city']
            if old_city != ctx.city:
                logger.info(f"[FSM] 🏙️  Город: {old_city} → {ctx.city}")
        
        if 'hours' in ai_data and ai_data['hours']:
            old_hours = ctx.hours
            ctx.hours = ai_data['hours']
            if old_hours != ctx.hours:
                logger.info(f"[FSM] ⏰ Часы: {old_hours} → {ctx.hours}")
        
        if 'people' in ai_data and ai_data['people']:
            old_people = ctx.people
            ctx.people = ai_data['people']
            if old_people != ctx.people:
                logger.info(f"[FSM] 👥 Грузчиков: {old_people} → {ctx.people}")
        
        if 'work_type' in ai_data and ai_data['work_type']:
            ctx.work_type = ai_data['work_type']
            logger.debug(f"[FSM] Тип работы: {ctx.work_type}")
        
        if 'ppr' in ai_data and ai_data['ppr']:
            ctx.ppr = ai_data['ppr']
        
        if 'min_hours' in ai_data and ai_data['min_hours']:
            ctx.min_hours = ai_data['min_hours']

