"""
Simple AI Processor - Production-Grade Architecture

PRINCIPLE: ONE AI CALL → EXTRACT ALL → VALIDATE → TEMPLATE

NO HALLUCINATION - AI не генерирует текст свободно!
"""
import json
import logging
from typing import Dict, Any, Optional, Tuple
import openai

from .schemas import EXTRACTION_SCHEMA, EXTRACTION_PROMPT
from .templates import TEMPLATES, format_template
from .rules import BusinessRules
from .pricing import PricingCalculator
from .context import DialogueContextManager
from .function_handlers import (
    execute_function,
    handle_create_bitrix_deal,
    handle_create_bitrix_deal_legal
)
from .config import DEFAULT_MODEL
from .micro_prompts import build_micro_prompt

import sys
sys.path.insert(0, '/home/ludskoe/kwork/pepsiai/se_base')
from chats_log import api as chats_log

logger = logging.getLogger(__name__)


class SimpleAIProcessor:
    """
    Упрощенный AI процессор
    
    Алгоритм:
    1. ONE AI CALL: извлечь ВСЕ данные (structured output)
    2. BUSINESS RULES: определить customer_type, действия (NO AI!)
    3. TEMPLATE: выбрать и заполнить шаблон (NO AI!)
    4. DONE: вернуть ответ
    
    Результат: NO HALLUCINATION, FAST, CHEAP
    """
    
    def __init__(self):
        logger.info("Инициализация SimpleAIProcessor")
        
        self.pricing_calculator = PricingCalculator()
        self.context_manager = DialogueContextManager()
        self.business_rules = BusinessRules()
        
        self._init_openai_client()
        
        # State
        self._last_extracted_data = {}
        self._last_customer_type = 'unknown'
    
    def _init_openai_client(self):
        """Инициализация OpenAI"""
        import config
        try:
            api_key = config.Production.OPENAI_API_KEY
            base_url = config.Production.OPENAI_BASE_URL
            
            self.openai_client = openai.OpenAI(api_key=api_key, base_url=base_url)
            
            # Test connection
            test_response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
                timeout=10
            )
            
            logger.info("✅ OpenAI client initialized")
            self.use_openai = True
            
        except Exception as e:
            logger.error(f"❌ OpenAI initialization failed: {e}")
            self.openai_client = None
            self.use_openai = False
    
    def process(
        self, 
        message: str, 
        chat_id: str = None,
        ad_data: dict = None,
        avito_message_model = None,
        return_metadata: bool = False
    ) -> Any:
        """
        Главный метод обработки сообщения
        
        Args:
            message: Текст сообщения
            chat_id: ID чата
            ad_data: Данные объявления
            avito_message_model: Модель для логирования (optional)
            return_metadata: Вернуть metadata
        
        Returns:
            str: Ответ для клиента
            или (str, dict): (ответ, metadata) если return_metadata=True
        """
        import time
        start_time = time.time()
        
        logger.info(f"Processing: '{message[:50]}...'")
        
        try:
            # Add to context
            if chat_id:
                self.context_manager.add_message(chat_id, message, is_user=True)
            
            # 1. EXTRACT ALL DATA (ONE AI CALL)
            extracted = self._extract_all_data(message, chat_id)
            self._last_extracted_data = extracted
            
            logger.info(f"📊 Extracted: intent={extracted['intent']}, "
                       f"city={extracted.get('city')}, "
                       f"people={extracted.get('people')}, "
                       f"keywords={extracted.get('keywords', [])}")
            
            # 2. BUSINESS RULES (NO AI!)
            response, metadata = self._apply_business_logic(message, extracted, chat_id, ad_data)
            
            # 3. LOG TO chats_log (для KPI Dashboard)
            response_time_ms = int((time.time() - start_time) * 1000)
            self._log_interaction(
                chat_id=chat_id,
                message=message,
                response=response,
                metadata=metadata,
                extracted=extracted,
                response_time_ms=response_time_ms,
                avito_message_model=avito_message_model
            )
            
            # Add to context
            if chat_id:
                self.context_manager.add_message(chat_id, response, is_user=False)
            
            if return_metadata:
                return response, metadata
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in process(): {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # 🚨 АЛЕРТ АДМИНАМ при критической ошибке
            try:
                import bot
                error_msg = (
                    f"🚨 CRITICAL: SimpleAIProcessor.process() failed\n\n"
                    f"Chat: {chat_id}\n"
                    f"Message: {message[:100]}\n"
                    f"Error: {str(e)[:200]}\n\n"
                    f"Trace: {traceback.format_exc()[:400]}"
                )
                bot.send_message(error_msg)
                logger.info("✅ Critical error alert sent")
            except Exception as alert_err:
                logger.error(f"Failed to send alert: {alert_err}")
            
            # Fallback ответ
            fallback = format_template('error_fallback')
            
            # Логируем ошибку
            if avito_message_model:
                try:
                    self._log_interaction(
                        message=message,
                        response=fallback,
                        chat_id=chat_id,
                        extracted={'intent': 'error', 'city': '', 'people': 0, 'hours': 0, 'phone': ''},
                        metadata={'action': 'error_fallback', 'error': str(e)[:200]},
                        response_time_ms=0,
                        avito_message_model=avito_message_model
                    )
                except Exception as log_err:
                    logger.error(f"Failed to log error: {log_err}")
            
            if return_metadata:
                return fallback, {'error': str(e), 'action': 'error_fallback'}
            return fallback
    
    def _extract_all_data(self, message: str, chat_id: str = None) -> Dict[str, Any]:
        """
        ОДИН AI CALL извлекает ВСЕ данные
        
        Использует Structured Output (JSON mode) - NO HALLUCINATION!
        """
        if not self.use_openai:
            logger.warning("OpenAI not available, using fallback")
            return self._fallback_extraction(message)
        
        try:
            context_messages = []
            if chat_id:
                try:
                    history = chats_log.get_chat_history(chat_id, limit=5)
                    context_messages = history[-5:] if history else []
                    logger.debug(f"Загружена история из БД: {len(context_messages)} сообщений")
                except Exception as history_err:
                    logger.error(f"Ошибка загрузки истории из БД: {history_err}")
                    history = self.context_manager.get_openai_messages(chat_id, limit=3)
                    context_messages = history[-3:] if history else []
            
            messages = context_messages + [
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": message}
            ]
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "data_extraction",
                        "strict": True,
                        "schema": EXTRACTION_SCHEMA
                    }
                },
                temperature=0,
                max_tokens=500
            )
            
            extracted = json.loads(response.choices[0].message.content)
            logger.info(f"ai extracted data: {extracted}")
            
            if chat_id and hasattr(self, '_last_extracted_data'):
                previous = self._last_extracted_data
                if not extracted.get('city') and previous.get('city'):
                    extracted['city'] = previous['city']
                if not extracted.get('people') and previous.get('people'):
                    extracted['people'] = previous['people']
                if not extracted.get('hours') and previous.get('hours'):
                    extracted['hours'] = previous['hours']
                if not extracted.get('phone') and previous.get('phone'):
                    extracted['phone'] = previous['phone']
                
                logger.info(f"📋 Merged with previous: city={extracted['city']}, people={extracted['people']}, hours={extracted['hours']}")
            
            return extracted
            
        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}")
            return self._fallback_extraction(message)
    
    def _fallback_extraction(self, message: str) -> Dict[str, Any]:
        """Fallback извлечение без AI (простые regex)"""
        import re
        
        extracted = {
            "intent": "ask_price",
            "city": "",
            "people": 0,
            "hours": 0,
            "phone": "",
            "keywords": [],
            "work_description": "",
            "has_special_items": False,
            "single_item_weight": 0,
            "floor": 0,
            "has_elevator": False,
            "urgency": "unknown",
            "is_forbidden_service": False,
            "confidence": 0.5
        }
        
        # Extract phone
        phone_match = re.search(r'(?:\+7|8|7)?[\s\-]?\(?(\d{3})\)?[\s\-]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})', message)
        if phone_match:
            extracted['phone'] = ''.join(phone_match.groups())
            extracted['intent'] = 'provide_phone'
        
        # Extract people
        people_match = re.search(r'(\d+)\s*(?:грузчик|человек|груз|ребят)', message.lower())
        if people_match:
            extracted['people'] = int(people_match.group(1))
        
        # Extract hours
        hours_match = re.search(r'(\d+)\s*(?:час|ч\b)', message.lower())
        if hours_match:
            extracted['hours'] = int(hours_match.group(1))
        
        # Extract city (simple patterns)
        for city in ['москв', 'петербург', 'казан', 'екатеринбург', 'новосибирск', 'самар', 'краснодар', 'ростов']:
            if city in message.lower():
                if city == 'москв':
                    extracted['city'] = 'Москва'
                elif city == 'петербург':
                    extracted['city'] = 'Санкт-Петербург'
                elif city == 'казан':
                    extracted['city'] = 'Казань'
                break
        
        # Extract keywords
        for keyword in ['офис', 'счет', 'договор', 'юрлиц', 'компани', 'квартир', 'переезд', 'такелаж', 'сейф', 'пианино']:
            if keyword in message.lower():
                extracted['keywords'].append(keyword)
        
        return extracted
    
    def _count_repeated_actions(self, chat_id: str) -> Dict[str, int]:
        """
        Подсчитать сколько раз каждое действие повторялось подряд
        
        Returns:
            {"action_name": count, ...}
        """
        if not chat_id:
            return {}
        
        history = self.context_manager.get_context(chat_id, limit=10)
        action_counts = {}
        last_action = None
        consecutive_count = 0
        
        for msg in reversed(history):
            if msg.get('is_user'):
                continue
            
            # Попробуем извлечь action из metadata (если сохранялся)
            # Или из шаблона сообщения
            msg_text = msg.get('message', '')
            
            # Простая эвристика: определяем action по паттернам
            current_action = None
            if 'Подтвердите' in msg_text or 'уточнит' in msg_text.lower():
                current_action = 'clarify'
            elif 'телефон' in msg_text.lower() and 'оставьте' in msg_text.lower():
                current_action = 'ask_phone'
            elif 'город' in msg_text.lower():
                current_action = 'ask_city'
            elif 'Сколько' in msg_text:
                current_action = 'ask_details'
            
            if current_action:
                if current_action == last_action:
                    consecutive_count += 1
                else:
                    if last_action:
                        action_counts[last_action] = consecutive_count
                    last_action = current_action
                    consecutive_count = 1
        
        if last_action:
            action_counts[last_action] = consecutive_count
        
        return action_counts
    
    def _analyze_context_with_ai(self, extracted: Dict, chat_id: str = None) -> Dict[str, Any]:
        """
        AI-анализ контекста диалога для умного определения:
        - Тип клиента (учитывая весь контекст, не только keywords)
        - Следующее действие (если застряли)
        - Готовность к сделке
        """
        if not self.use_openai or not chat_id:
            return {
                'customer_type': 'unknown',
                'customer_confidence': 0.5,
                'next_action': 'ask_details',
                'reasoning': 'AI unavailable',
                'ready_for_deal': False
            }
        
        try:
            history = self.context_manager.get_context(chat_id, limit=6)
            
            # Форматируем историю
            history_text = ""
            for i, msg in enumerate(history[-6:], 1):
                role = "Клиент" if msg.get('is_user') else "Бот"
                history_text += f"{i}. {role}: {msg.get('message', '')}\n"
            
            context_prompt = f"""Ты эксперт по анализу диалогов службы грузчиков.

ИСТОРИЯ ДИАЛОГА:
{history_text}

ИЗВЛЕЧЕННЫЕ ДАННЫЕ:
Город: {extracted.get('city', 'не указан')}
Грузчиков: {extracted.get('people', 0)}
Часов: {extracted.get('hours', 0)}
Телефон: {'есть' if extracted.get('phone') else 'нет'}
Ключевые слова: {', '.join(extracted.get('keywords', [])) or 'нет'}
Описание: {extracted.get('work_description', '')}

ЗАДАЧИ АНАЛИЗА:

1. ТИП КЛИЕНТА (customer_type):
   - "legal" если: смена, овощебаза, склад, магазин, офис, регулярно, >4 грузчиков, >8 часов, счет, договор
   - "private" если: переезд, квартира, дача, дом, мебель, вещи, разовая работа
   - "unknown" если неясно

2. СЛЕДУЮЩЕЕ ДЕЙСТВИЕ (next_action):
   - "ask_phone" если: клиент подтвердил ("да", "верно", "согласен"), ИЛИ есть все данные (город+люди+часы), ИЛИ диалог застрял
   - "show_price" если: есть город+люди+часы, клиент спрашивает цену, тип=private
   - "ask_details" если: не хватает людей или часов
   - "ask_city" если: нет города
   - "clarify_customer_type" если: неясно юрлицо или частник, но есть все данные

3. ГОТОВНОСТЬ К СДЕЛКЕ (ready_for_deal):
   - true если: есть город AND (люди OR часы) AND тип клиента определен с уверенностью >0.6
   - false если чего-то не хватает

4. АНАЛИЗ ЗАЦИКЛИВАНИЯ:
   - Если бот >2 раз спрашивает одно и то же → next_action = "ask_phone" (выход из цикла)

Верни ТОЛЬКО JSON (без markdown):
{{
  "customer_type": "legal|private|unknown",
  "customer_confidence": 0.8,
  "next_action": "ask_phone",
  "reasoning": "Овощебаза + смена 12ч + 4 грузчика = юрлицо. Клиент подтвердил → просим телефон",
  "ready_for_deal": true
}}"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": context_prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=300
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"🧠 AI Context Analysis: {result['customer_type']} ({result['customer_confidence']:.2f}) → {result['next_action']}")
            logger.info(f"   Reasoning: {result['reasoning']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Context analysis failed: {e}")
            return {
                'customer_type': 'unknown',
                'customer_confidence': 0.5,
                'next_action': 'ask_details',
                'reasoning': f'Error: {e}',
                'ready_for_deal': False
            }
    
    def _log_interaction(
        self,
        chat_id: str,
        message: str,
        response: str,
        metadata: Dict[str, Any],
        extracted: Dict[str, Any] = None,
        response_time_ms: int = None,
        avito_message_model = None
    ):
        """
        Логирование взаимодействия в chats_log для KPI Dashboard
        
        Args:
            chat_id: ID чата
            message: Сообщение клиента
            response: Ответ бота
            metadata: Метаданные обработки
            extracted: Извлеченные данные
            response_time_ms: Время обработки в мс
            avito_message_model: Модель для полного логирования (optional)
        """
        try:
            if not chat_id:
                return
            
            # Комментарий для логирования
            comment_parts = []
            if metadata.get('customer_type'):
                comment_parts.append(f"Type:{metadata['customer_type']}")
            if metadata.get('action'):
                comment_parts.append(f"Action:{metadata['action']}")
            if metadata.get('deal_created'):
                comment_parts.append("DealCreated")
            if metadata.get('ai_override'):
                comment_parts.append("AI_Override")
            
            comment = " | ".join(comment_parts) if comment_parts else "No metadata"
            
            # Логирование в chats_log (для KPI Dashboard)
            if avito_message_model:
                try:
                    chats_log.create_chat_log(
                        model=avito_message_model,
                        is_success=True,
                        answer=response,
                        comment=comment,
                        extracted_data=extracted,
                        function_calls=None,  # Не используем function calls в новой архитектуре
                        quality_score=metadata.get('customer_type_confidence'),
                        experiment_variant='simple_processor_ai_over_ai',
                        deal_created=metadata.get('deal_created', False),
                        deal_id=metadata.get('deal_id'),
                        response_time_ms=response_time_ms
                    )
                    logger.info(f"✅ Logged to chats_log: {chat_id}")
                except Exception as log_error:
                    logger.error(f"❌ Failed to log to chats_log: {log_error}")
            
            logger.info(f"📝 Interaction logged: {chat_id} | {comment}")
            
        except Exception as e:
            logger.error(f"❌ Error logging interaction: {e}")
    
    def _generate_response(
        self,
        message: str,
        action: str,
        customer_type: str,
        extracted: Dict[str, Any],
        pricing: Dict = None,
        chat_id: str = None
    ) -> str:
        """
        Генерация живого ответа через OpenAI с микро-промптом
        
        Args:
            message: Сообщение клиента
            action: Действие (ask_city, show_price, etc)
            customer_type: Тип клиента
            extracted: Извлеченные данные
            pricing: Данные о ценах
            chat_id: ID чата (для контекста)
        
        Returns:
            Сгенерированный ответ
        """
        try:
            context_messages = []
            is_first_message = True
            bot_message_count = 0
            
            if chat_id:
                try:
                    history = chats_log.get_chat_history(chat_id, limit=5)
                    if history:
                        bot_message_count = len([m for m in history if m.get('role') == 'assistant'])
                        is_first_message = (bot_message_count == 0)
                        logger.debug(f"is_first_message={is_first_message}, bot_messages={bot_message_count}")
                        
                        # Последние 3 сообщения для контекста
                        context_messages = history[-3:] if len(history) >= 3 else history
                except Exception as history_err:
                    logger.error(f"Ошибка загрузки истории из БД для is_first_message: {history_err}")
                    # Fallback на in-memory context
                    history = self.context_manager.get_context(chat_id)
                    if history:
                        bot_message_count = len([m for m in history if not m.get('is_user')])
                        is_first_message = (bot_message_count == 0)
                        recent = history[-3:] if len(history) >= 3 else history
                        for msg in recent:
                            role = "user" if msg.get('is_user') else "assistant"
                            context_messages.append({
                                "role": role,
                                "content": msg.get('message', '')
                            })

            micro_prompt = build_micro_prompt(action, customer_type, extracted, pricing, is_first_message)
            
            messages = [
                {"role": "system", "content": micro_prompt}
            ]
            
            if context_messages:
                messages.extend(context_messages)
            
            messages.append({"role": "user", "content": message})
            
            logger.info(f"🎨 Generating response for action='{action}'")
            
            response = self.openai_client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                temperature=0.7,  # Больше креативности
                max_tokens=300
            )
            
            generated = response.choices[0].message.content.strip()
            logger.info(f"✅ Generated: {generated[:100]}...")
            
            return generated
            
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}")
            # Fallback к шаблону
            return format_template(self._action_to_template(action), **extracted)
    
    def _action_to_template(self, action: str) -> str:
        """Маппинг action -> template_id для fallback"""
        mapping = {
            'greeting': 'greeting',
            'ask_city': 'need_city',
            'ask_details': 'need_details',
            'ask_phone_legal': 'legal_no_price',
            'show_price_ask_phone': 'private_with_price',
            'reject_forbidden': 'forbidden_body_transport',
            'reject_min_workers': 'min_2_workers',
            'ask_phone_tackling': 'tackling_need_details',
            'city_not_available': 'city_not_in_list',
            'deal_created': 'deal_created',
        }
        return mapping.get(action, 'error_fallback')
    
    def _apply_business_logic(
        self,
        message: str,
        extracted: Dict[str, Any],
        chat_id: str = None,
        ad_data: dict = None
    ) -> Tuple[str, Dict]:
        """
        Применить бизнес-правила и выбрать template
        
        NO AI - только логика!
        
        Returns:
            (response_text, metadata)
        """
        metadata = {
            'extracted': extracted,
            'customer_type': 'unknown',
            'action': 'unknown',
            'template_id': None,
            'deal_created': False
        }
        
        if extracted.get('is_forbidden_service', False):
        
            metadata['action'] = 'reject_forbidden'
            metadata['template_id'] = 'forbidden_body_transport'
            metadata['forbidden_reason'] = 'AI_detected'
            response = self._generate_response(message, 'reject_forbidden', 'unknown', extracted, chat_id=chat_id)
            return response, metadata
        
        is_forbidden, reason = self.business_rules.check_forbidden(extracted)
        if is_forbidden:
            metadata['action'] = 'reject_forbidden'
            metadata['template_id'] = 'forbidden_body_transport'
            metadata['forbidden_reason'] = f'keyword:{reason}'
            response = self._generate_response(message, 'reject_forbidden', 'unknown', extracted, chat_id=chat_id)
            return response, metadata
        
        is_floor_restricted, floor_reason = self.business_rules.check_floor_restriction(extracted)
        if is_floor_restricted:
            metadata['action'] = 'reject_floor_restriction'
            metadata['template_id'] = 'floor_restriction'
            extracted['floor'] = extracted.get('floor', 0)
            response = self._generate_response(message, 'reject_floor_restriction', 'unknown', extracted, chat_id=chat_id)
            return response, metadata
        
        is_heavy_item, heavy_reason = self.business_rules.check_heavy_item(extracted)
        if is_heavy_item:
            phone = extracted.get('phone', '')
            extracted['weight'] = extracted.get('single_item_weight', 0)
            if phone and phone != '':
                metadata['action'] = 'create_tackling_deal'
                metadata['deal_created'] = True
                metadata['template_id'] = 'heavy_item_tackling'
                response = self._generate_response(message, 'deal_created', 'unknown', extracted, chat_id=chat_id)
                return response, metadata
            else:
                metadata['action'] = 'ask_phone_tackling'
                metadata['template_id'] = 'heavy_item_tackling'
                response = self._generate_response(message, 'ask_phone_tackling', 'unknown', extracted, chat_id=chat_id)
                return response, metadata

        customer_type, confidence = self.business_rules.detect_customer_type(extracted)
        self._last_customer_type = customer_type
        metadata['customer_type'] = customer_type
        metadata['customer_type_confidence'] = confidence
        
        logger.info(f"🎯 Customer type: {customer_type} (confidence: {confidence:.2f})")
        
        # 🧠 AI CONTEXT ANALYZER: проверка зацикливания и уточнение типа клиента
        repeated_actions = self._count_repeated_actions(chat_id)
        is_stuck = any(count >= 2 for count in repeated_actions.values())
        
        if is_stuck or confidence < 0.7:
            if is_stuck:
                logger.warning(f"⚠️ Dialogue stuck: {repeated_actions}")
            
            ai_context = self._analyze_context_with_ai(extracted, chat_id)
            
            # Override customer_type если AI более уверен
            if ai_context['customer_confidence'] > confidence:
                customer_type = ai_context['customer_type']
                confidence = ai_context['customer_confidence']
                metadata['customer_type'] = customer_type
                metadata['customer_type_confidence'] = confidence
                metadata['ai_override'] = True
                logger.info(f"🤖 AI override customer_type: {customer_type} ({confidence:.2f})")
            
            # Если AI говорит ask_phone и ready_for_deal → выходим из зацикливания
            if ai_context['next_action'] == 'ask_phone' and ai_context['ready_for_deal']:
                phone = extracted.get('phone', '')
                if not phone:
                    logger.info(f"🚀 AI suggests: ask_phone (breaking loop)")
                    
                    if customer_type == 'legal':
                        metadata['action'] = 'ask_phone_legal'
                        metadata['template_id'] = 'legal_no_price'
                        response = self._generate_response(message, 'ask_phone_legal', 'legal', extracted, chat_id=chat_id)
                        return response, metadata
                    else:
                        # Для private: попробуем показать цену если есть все данные
                        city = extracted.get('city', '')
                        people = extracted.get('people', 0)
                        hours = extracted.get('hours', 0)
                        
                        if city and people and hours:
                            pricing = self.pricing_calculator.get_city_pricing(city)
                            if pricing:
                                ppr = pricing['ppr']
                                min_hours = pricing['min_hours']
                                hours_charged = max(hours, min_hours)
                                total = people * hours_charged * ppr
                                
                                pricing_data = {
                                    'city': city,
                                    'ppr': ppr,
                                    'min_hours': min_hours,
                                    'people': people,
                                    'hours': hours,
                                    'hours_charged': hours_charged,
                                    'total': total
                                }
                                
                                metadata['action'] = 'show_price_ask_phone'
                                metadata['template_id'] = 'private_with_price'
                                metadata['pricing'] = pricing_data
                                response = self._generate_response(message, 'show_price_ask_phone', 'private', extracted, pricing_data, chat_id=chat_id)
                                return response, metadata
                        
                        # Если нет всех данных - просто спросим телефон
                        metadata['action'] = 'ask_phone'
                        metadata['template_id'] = 'need_phone'
                        response = self._generate_response(message, 'ask_phone', customer_type, extracted, chat_id=chat_id)
                        return response, metadata
        
        # 3. Check tackling
        is_tackling = self.business_rules.check_tackling(extracted)
        if is_tackling:
            phone = extracted.get('phone', '')
            if phone and phone != '':
                # Create deal for tackling
                metadata['action'] = 'create_tackling_deal'
                metadata['deal_created'] = True
                metadata['template_id'] = 'tackling_deal_created'
                response = self._generate_response(message, 'deal_created', customer_type, extracted, chat_id=chat_id)
                return response, metadata
            else:
                metadata['action'] = 'ask_phone_tackling'
                metadata['template_id'] = 'tackling_need_phone'
                response = self._generate_response(message, 'ask_phone_tackling', customer_type, extracted, chat_id=chat_id)
                return response, metadata
        
        if customer_type == 'private':
            people = extracted.get('people', 0)
            if people > 0 and people < 2:
                metadata['action'] = 'reject_min_workers'
                metadata['template_id'] = 'min_2_workers'
                response = self._generate_response(message, 'reject_min_workers', customer_type, extracted, chat_id=chat_id)
                return response, metadata
        
        if customer_type == 'legal':
            return self._handle_legal_entity(message, extracted, metadata, chat_id)
        elif customer_type == 'private':
            return self._handle_private_customer(message, extracted, metadata, ad_data, chat_id)
        else:
            # Unknown - need more info
            return self._handle_unknown_customer(message, extracted, metadata, chat_id)
    
    def _handle_legal_entity(self, message: str, extracted: Dict, metadata: Dict, chat_id: str = None) -> Tuple[str, Dict]:
        """Обработка юрлица"""
        phone = extracted.get('phone', '')
        if phone and phone != '':
            deal_result = handle_create_bitrix_deal_legal(
                arguments={
                    'phone': phone,
                    'city': extracted.get('city', ''),
                    'hours': extracted.get('hours', 0),
                    'people': extracted.get('people', 0),
                    'work_type': extracted.get('work_description', ''),
                    'summary': extracted.get('work_description', ''),
                    'company_name': extracted.get('company_name', '')
                },
                context={'chat_id': chat_id}
            )
            
            if deal_result.get('success'):
                extracted['deal_id'] = deal_result.get('deal_id', '???')
                metadata['deal_id'] = deal_result.get('deal_id')
                metadata['action'] = 'create_legal_deal'
                metadata['deal_created'] = True
                metadata['template_id'] = 'legal_with_phone'
                logger.info(f"✅ Legal deal created: #{deal_result.get('deal_id')}")
                response = self._generate_response(message, 'deal_created', 'legal', extracted, chat_id=chat_id)
                return response, metadata
            else:
                # Битрикс недоступен - не врем клиенту
                logger.error(f"❌ Failed to create legal deal: {deal_result.get('error')}")
                metadata['action'] = 'bitrix_unavailable'
                metadata['deal_created'] = False
                metadata['template_id'] = 'bitrix_unavailable'
                metadata['error'] = deal_result.get('error', 'unknown')
                response = self._generate_response(message, 'bitrix_unavailable', 'legal', extracted, chat_id=chat_id)
                return response, metadata
        else:
            metadata['action'] = 'ask_phone_legal'
            metadata['template_id'] = 'legal_no_price'
            response = self._generate_response(message, 'ask_phone_legal', 'legal', extracted, chat_id=chat_id)
            return response, metadata
    
    def _handle_private_customer(
        self,
        message: str,
        extracted: Dict, 
        metadata: Dict,
        ad_data: dict = None,
        chat_id: str = None
    ) -> Tuple[str, Dict]:
        """Обработка физлица"""
        city = extracted.get('city', '')
        people = extracted.get('people', 0)
        hours = extracted.get('hours', 0)
        phone = extracted.get('phone', '')
        
        # Need city?
        if not city or city == '':
            metadata['action'] = 'ask_city'
            metadata['template_id'] = 'need_city'
            response = self._generate_response(message, 'ask_city', 'private', extracted, chat_id=chat_id)
            return response, metadata
        
        # Check if city in pricing
        pricing = self.pricing_calculator.get_city_pricing(city)
        if not pricing:
            metadata['action'] = 'city_not_available'
            metadata['template_id'] = 'city_not_in_list'
            extracted['city'] = city  # For prompt
            response = self._generate_response(message, 'city_not_available', 'private', extracted, chat_id=chat_id)
            return response, metadata
        
        # Need details?
        if not people or people == 0 or not hours or hours == 0:
            metadata['action'] = 'ask_details'
            metadata['template_id'] = 'need_details'
            response = self._generate_response(message, 'ask_details', 'private', extracted, chat_id=chat_id)
            return response, metadata
        
        # Calculate price
        ppr = pricing['ppr']
        min_hours = pricing['min_hours']
        hours_to_charge = max(hours, min_hours)
        total = people * hours_to_charge * ppr
        
        pricing_data = {
            'city': city,
            'ppr': ppr,
            'min_hours': min_hours,
            'people': people,
            'hours': hours,
            'hours_charged': hours_to_charge,
            'total': total
        }
        
        metadata['pricing'] = pricing_data
        
        if phone:
            deal_result = handle_create_bitrix_deal(
                arguments={
                    'phone': phone,
                    'city': city,
                    'hours': hours,
                    'people': people,
                    'price': total,
                    'summary': extracted.get('work_description', ''),
                    'floor': extracted.get('floor', 0),
                    'has_elevator': extracted.get('has_elevator', False)
                },
                context={'chat_id': chat_id}
            )
            
            if deal_result.get('success'):
                extracted['deal_id'] = deal_result.get('deal_id', '???')
                metadata['deal_id'] = deal_result.get('deal_id')
                metadata['action'] = 'create_private_deal'
                metadata['deal_created'] = True
                metadata['template_id'] = 'deal_created'
                logger.info(f"✅ Private deal created: #{deal_result.get('deal_id')}")
                response = self._generate_response(message, 'deal_created', 'private', extracted, pricing_data, chat_id=chat_id)
                return response, metadata
            else:
                # Битрикс недоступен - не врем клиенту
                logger.error(f"❌ Failed to create private deal: {deal_result.get('error')}")
                metadata['action'] = 'bitrix_unavailable'
                metadata['deal_created'] = False
                metadata['template_id'] = 'bitrix_unavailable'
                metadata['error'] = deal_result.get('error', 'unknown')
                response = self._generate_response(message, 'bitrix_unavailable', 'private', extracted, pricing_data, chat_id=chat_id)
                return response, metadata
        else:
            # Show price, ask phone
            metadata['action'] = 'show_price_ask_phone'
            metadata['template_id'] = 'private_with_price'
            response = self._generate_response(message, 'show_price_ask_phone', 'private', extracted, pricing_data, chat_id=chat_id)
            return response, metadata
    
    def _handle_unknown_customer(self, message: str, extracted: Dict, metadata: Dict, chat_id: str = None) -> Tuple[str, Dict]:
        """Обработка когда тип клиента неизвестен"""
        # Check if large order - need clarification
        if self.business_rules.should_clarify_large_order(extracted, 'unknown'):
            metadata['action'] = 'clarify_large_order'
            metadata['template_id'] = 'clarify_large_order'
            response = self._generate_response(message, 'clarify_large_order', 'unknown', extracted, chat_id=chat_id)
            return response, metadata
        
        # Need more info
        city = extracted.get('city', '')
        if not city or city == '':
            metadata['action'] = 'ask_city'
            metadata['template_id'] = 'need_city'
            response = self._generate_response(message, 'ask_city', 'unknown', extracted, chat_id=chat_id)
            return response, metadata
        
        metadata['action'] = 'ask_details'
        metadata['template_id'] = 'need_details'
        response = self._generate_response(message, 'ask_details', 'unknown', extracted, chat_id=chat_id)
        return response, metadata

