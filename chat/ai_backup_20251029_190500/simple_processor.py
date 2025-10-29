"""
Simple AI Processor V2 - Минимализм

ПРИНЦИП: 
1 AI вызов (извлечь JSON с флагами) → if-else по флагам → Шаблон → Ответ

NO BULLSHIT:
- Нет Context Analyzer
- Нет AI генерации текста
- Нет confidence проверок
- Нет магических чисел
"""
import json
import logging
import time
from typing import Dict, Any, Tuple

import openai

import sys
sys.path.insert(0, '/home/ludskoe/kwork/pepsiai/se_base')
from chats_log import api as chats_log
from db import Session

logger = logging.getLogger(__name__)

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "city": {"type": "string"},
        "people": {"type": "integer"},
        "hours": {"type": "number"},
        "phone": {"type": "string"},
        "floor": {"type": "integer"},
        "has_elevator": {"type": "boolean"},
        "single_item_weight": {"type": "integer"},
        
        # ФЛАГИ (AI РЕШАЕТ!)
        "is_greeting": {
            "type": "boolean",
            "description": "TRUE если клиент ТОЛЬКО здоровается (привет, здравствуйте, добрый день)"
        },
        "is_forbidden_service": {
            "type": "boolean",
            "description": "TRUE если запрос на перенос ЛЮДЕЙ (деда, старика, больного, покойника)"
        },
        "needs_tackling": {
            "type": "boolean", 
            "description": "TRUE если сейф/пианино/рояль/станок/банкомат (вес >70кг одного предмета или спецпредмет)"
        },
        "is_legal_client": {
            "type": "boolean",
            "description": "TRUE если юрлицо: офис, склад, магазин, овощебаза, организация, компания, договор, счет, ИНН, юрлицо, тех.задание, оборудование, станки, техника, стеллажи, такелаж, кран, спецтехника, большой тоннаж (5 тонн, 10 тонн), регулярно, постоянно, на месяц, >4 грузчиков"
        },
        "needs_transport": {
            "type": "boolean",
            "description": "TRUE если клиент спрашивает про машину/газель/авто/транспорт ('есть машина?', 'нужна газель')"
        },
        "has_question": {
            "type": "boolean",
            "description": "TRUE если это ВОПРОС (не сбор данных): про услуги, условия, время работы, упаковку, выходные и т.д."
        }
    },
    "required": ["city", "people", "hours", "phone", "floor", "has_elevator", 
                 "single_item_weight", "is_greeting", "is_forbidden_service", "needs_tackling", 
                 "is_legal_client", "needs_transport", "has_question"],
    "additionalProperties": False
}

EXTRACTION_PROMPT = """Извлеки данные из сообщения клиента службы грузчиков.

⚠️ ВАЖНО: Если клиент ТОЛЬКО здоровается БЕЗ данных - НЕ придумывай city/people/hours! Оставь пустыми.

ФЛАГИ:
- is_greeting: TRUE если клиент ТОЛЬКО здоровается (привет, здравствуйте, добрый день) БЕЗ других данных
- is_forbidden_service: TRUE если клиент просит перенести ЧЕЛОВЕКА (деда, старика, бабушку, больного, покойника, инвалида)
- needs_tackling: TRUE если сейф/пианино/рояль/станок/банкомат ИЛИ вес одного предмета >70кг
- is_legal_client: TRUE если юрлицо (офис, склад, оборудование, тоннаж 5+ тонн, договор, счет, регулярно, >4 грузчиков)
- needs_transport: TRUE если спрашивает про машину/газель/транспорт
- has_question: TRUE если ВОПРОС (не данные): про услуги, условия, время, упаковку

Примеры:
"Здравствуйте" → is_greeting: true, city: "", people: 0, hours: 0
"Привет, нужны 2 грузчика" → is_greeting: false (есть данные!)
"Нужно вынести старика" → is_forbidden_service: true
"Поднять сейф" → needs_tackling: true
"Грузчики для офиса, счет" → is_legal_client: true
"Переместить оборудование 5 тонн" → is_legal_client: true
"А машина есть?" → needs_transport: true, has_question: true
"Работаете в выходные?" → has_question: true
"""


AI_DISCLAIMER = "💬 Я AI-бот SE Express. "

TEMPLATES = {
    "greeting": "Здравствуйте! Чем могу помочь? 😊",
    
    "forbidden": "Извините, мы не оказываем услуги по перевозке людей. Будем рады помочь с переездом или грузоперевозками!",
    
    "floor_restriction": "К сожалению, мы работаем только до 3 этажа без лифта. Приносим извинения за неудобства!",
    
    "tackling_ask_phone": "Для перемещения тяжелых предметов требуется персональный расчет. Пожалуйста, оставьте номер телефона, и наш менеджер рассчитает стоимость.",
    
    "legal_ask_phone": "Для юридических лиц и больших объемов мы готовим персональное предложение с договором и счетом. Оставьте, пожалуйста, номер телефона менеджера.",
    
    "transport_ask_phone": "Газель: 2000₽/час (минимум 2 часа) + минимум 2 грузчика. Оставьте номер телефона для точного расчета с учетом всех деталей.",
    
    "question_ask_phone": "Отличный вопрос! Давайте я уточню детали у менеджера. Пожалуйста, оставьте номер телефона.",
    
    "city_not_found": "К сожалению, мы пока не работаем в городе {city}. Оставьте номер телефона, и наш менеджер уточнит возможность выполнения заказа.",
    
    "ask_city": "Подскажите, пожалуйста, в каком городе вам нужны грузчики?",
    
    "ask_details": "Отлично! Сколько грузчиков и на сколько часов нужно в городе {city}?",
    
    "show_price": "Стоимость работы в городе {city}: {price}₽ ({people} грузчиков × {hours}ч). Оставьте номер телефона, и мы оформим заказ.",
    
    "deal_created": "Отлично! Заявка #{deal_id} создана. Наш менеджер свяжется с вами в течение 15 минут. Спасибо за обращение!",
    
    "error": "Приносим извинения, произошла техническая ошибка. Пожалуйста, оставьте номер телефона, и мы обязательно вам перезвоним."
}


class SimpleAIProcessor:
    """Упрощенный процессор: 1 AI вызов → if-else → шаблон"""
    
    def __init__(self):
        logger.info("SimpleAIProcessor: Инициализация")
        self._init_openai()
        self._load_pricing()
        self.current_chat_id = None  # Для передачи в create_deal
    
    def _init_openai(self):
        import config
        try:
            self.openai_client = openai.OpenAI(
                api_key=config.Production.OPENAI_API_KEY,
                base_url=config.Production.OPENAI_BASE_URL
            )
            logger.info("✅ OpenAI client ready")
        except Exception as e:
            logger.error(f"❌ OpenAI init failed: {e}")
            self.openai_client = None
    
    def _load_pricing(self):
        """Загрузка прайсов из JSON"""
        try:
            import os
            pricing_path = os.path.join(os.path.dirname(__file__), '../../clean_pricing_data.json')
            with open(pricing_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.pricing = data.get('cities', {})
            logger.info(f"✅ Загружено {len(self.pricing)} городов")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки прайсов: {e}")
            self.pricing = {}
    
    def process(self, message: str, chat_id: str = None, ad_city: str = None, avito_message_model=None) -> str:
        """
        Главный метод: сообщение → ответ
        
        Args:
            message: Сообщение клиента
            chat_id: ID чата
            ad_city: Город из объявления Avito (опционально, как подсказка для AI)
            avito_message_model: Модель для логирования
        """
        start_time = time.time()
        self.current_chat_id = chat_id  # Сохраняем для create_deal
        
        try:
            extracted = self._extract_data(message, chat_id, ad_city)
            response, action = self._apply_rules(extracted)
            
            # Добавить disclaimer если первое сообщение
            is_first_message = self._is_first_message(chat_id)
            if is_first_message:
                response = AI_DISCLAIMER + response
            
            response_time_ms = int((time.time() - start_time) * 1000)
            self._log(chat_id, message, response, extracted, action, response_time_ms, avito_message_model)
            
            logger.info(f"✅ Response: {action} | City:{ad_city or 'N/A'} | First:{is_first_message} | {response_time_ms}ms")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return TEMPLATES["error"]
    
    def _is_first_message(self, chat_id: str) -> bool:
        """Проверка: это первое сообщение в чате?"""
        if not chat_id:
            return True
        
        try:
            with Session() as session:
                from chats_log.entities import ChatLog
                count = session.query(ChatLog).filter(
                    ChatLog.chat_id == chat_id,
                    ChatLog.is_success == True
                ).count()
                return count == 0
        except Exception as e:
            logger.error(f"Ошибка проверки is_first_message: {e}")
            return True
    
    def _extract_data(self, message: str, chat_id: str = None, ad_city: str = None) -> Dict[str, Any]:
        """
        AI извлечение: сообщение → JSON с флагами
        
        Args:
            message: Сообщение клиента
            chat_id: ID чата для истории
            ad_city: Город из объявления Avito (если известен)
        """
        if not self.openai_client:
            return self._fallback_extract(message)
        
        try:
            context = []
            if chat_id:
                try:
                    history = chats_log.get_chat_history(chat_id, limit=3)
                    context = history[-3:] if history else []
                except Exception as e:
                    logger.error(f"История не загружена: {e}")
            
            # Добавить подсказку о городе из объявления
            extraction_prompt = EXTRACTION_PROMPT
            if ad_city:
                extraction_prompt += f"\n\n🏙️ ПОДСКАЗКА: Город из объявления Avito = '{ad_city}'. Если клиент не указал другой город явно, используй этот."
            
            messages = context + [
                {"role": "system", "content": extraction_prompt},
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
                max_tokens=300
            )
            
            extracted = json.loads(response.choices[0].message.content)
            logger.info(f"📊 Extracted: city={extracted['city']}, people={extracted['people']}, "
                       f"forbidden={extracted['is_forbidden_service']}, tackling={extracted['needs_tackling']}")
            
            return extracted
            
        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}")
            return self._fallback_extract(message)
    
    def _fallback_extract(self, message: str) -> Dict:
        """Fallback если AI недоступен - пытаемся извлечь телефон regex"""
        import re
        phone_match = re.search(r'(\+?7|8)?[\s\-]?\(?(\d{3})\)?[\s\-]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})', message)
        phone = phone_match.group(0) if phone_match else ""
        
        return {
            "city": "",
            "people": 0,
            "hours": 0,
            "phone": phone,
            "floor": 0,
            "has_elevator": False,
            "single_item_weight": 0,
            "is_greeting": False,
            "is_forbidden_service": False,
            "needs_tackling": False,
            "is_legal_client": False,
            "needs_transport": False,
            "has_question": False,
            "_is_ai_unavailable": True  # Флаг что это fallback
        }
    
    def _apply_rules(self, extracted: Dict) -> Tuple[str, str]:
        """
        IF-ELSE по ФЛАГАМ (NO AI!)
        
        Returns:
            (response_text, action_name)
        """
        

        if extracted.get('_is_ai_unavailable'):
            if extracted.get('phone'):

                deal_id = self._create_deal(extracted, comment="⚠️ AI недоступен - требует проверки менеджером")
                return (f"Заявка создана! Наш менеджер свяжется с вами в ближайшее время.", "ai_unavailable_with_phone")
                else:
                return ("Пожалуйста, оставьте номер телефона, и наш менеджер свяжется с вами.", "ai_unavailable")
        
        # ПРИВЕТСТВИЕ (если is_greeting=True, игнорируем остальные данные)
        if extracted['is_greeting']:
            return (TEMPLATES["greeting"], "greeting")
        
        # ОТСЕВ #1: Запрещенные услуги
        if extracted['is_forbidden_service']:
            return (TEMPLATES["forbidden"], "forbidden")
        
        # ОТСЕВ #2: Этаж без лифта
        if extracted['floor'] > 3 and not extracted['has_elevator']:
            return (TEMPLATES["floor_restriction"], "floor_restriction")
        
        # ОТСЕВ #3: Такелаж ИЛИ юрлицо ИЛИ >5 часов
        if extracted['needs_tackling'] or extracted['is_legal_client'] or extracted['hours'] > 5:
            if not extracted['phone']:
                return (TEMPLATES["tackling_ask_phone"] if extracted['needs_tackling'] else TEMPLATES["legal_ask_phone"], 
                        "tackling_ask_phone" if extracted['needs_tackling'] else "legal_ask_phone")
            else:
                deal_id = self._create_deal_legal(extracted)
                return (TEMPLATES["deal_created"].format(deal_id=deal_id), "legal_deal_created")
        if extracted['needs_transport']:
            if not extracted['phone']:
                return (TEMPLATES["transport_ask_phone"], "transport_ask_phone")
            else:
                deal_id = self._create_deal(extracted, comment="Нужна Газель")
                return (TEMPLATES["deal_created"].format(deal_id=deal_id), "transport_deal_created")
        
        # ЛЮБОЙ ДРУГОЙ ВОПРОС
        if extracted['has_question']:
            if not extracted['phone']:
                return (TEMPLATES["question_ask_phone"], "question_ask_phone")
            else:
                deal_id = self._create_deal(extracted, comment="Вопрос клиента")
                return (TEMPLATES["deal_created"].format(deal_id=deal_id), "question_deal_created")
        
        # СБОР ДАННЫХ #1: Город
        if not extracted['city']:
            return (TEMPLATES["ask_city"], "ask_city")
        
        # ПРОВЕРКА: Город в базе
        if not self._city_in_database(extracted['city']):
            return (TEMPLATES["city_not_found"].format(city=extracted['city']), "city_not_found")
        
        # СБОР ДАННЫХ #2: Детали
        if not extracted['people'] or not extracted['hours']:
            city = extracted['city']
            return (TEMPLATES["ask_details"].format(city=city), "ask_details")
        
        # СБОР ДАННЫХ #3: Телефон + показ цены
        if not extracted['phone']:
            price = self._calculate_price(extracted)
            return (
                TEMPLATES["show_price"].format(
                    city=extracted['city'],
                    price=price,
                    people=extracted['people'],
                    hours=extracted['hours']
                ),
                "show_price"
            )
        
        deal_id = self._create_deal(extracted)
        return (TEMPLATES["deal_created"].format(deal_id=deal_id), "deal_created")
    
    def _city_in_database(self, city: str) -> bool:
        """Проверка города в базе"""
        if not city:
            return False
        return city in self.pricing
    
    def _calculate_price(self, extracted: Dict) -> int:
        """Расчет цены из clean_pricing_data.json"""
        city = extracted['city']
        people = extracted['people']
        hours = extracted['hours']
        
        if city not in self.pricing:
            return 0
        
        city_pricing = self.pricing[city]
        ppr = city_pricing.get('ppr', 200)
        min_hours = city_pricing.get('min_hours', 4.0)
        
        hours_charged = max(float(hours), min_hours)
        
        return int(people * hours_charged * ppr)
    
    def _create_deal(self, extracted: Dict, comment: str = "") -> str:
        """Создание обычной сделки в Битрикс"""
        try:
            from chat.ai.function_handlers import handle_create_bitrix_deal
            
            summary_parts = []
            if extracted.get('city'):
                summary_parts.append(f"Город: {extracted['city']}")
            if extracted.get('people'):
                summary_parts.append(f"Грузчики: {extracted['people']}")
            if extracted.get('hours'):
                summary_parts.append(f"Часы: {extracted['hours']}")
            if comment:
                summary_parts.append(comment)
            
            result = handle_create_bitrix_deal(
                arguments={
                    'phone': extracted['phone'],
                    'city': extracted.get('city', ''),
                    'hours': extracted.get('hours', 0),
                    'people': extracted.get('people', 0),
                    'summary': ' | '.join(summary_parts)
                },
                context={'chat_id': self.current_chat_id}
            )
            
            if result.get('success'):
                deal_id = result.get('deal_id', 'UNKNOWN')
                logger.info(f"✅ Deal created: #{deal_id}")
                return str(deal_id)
            else:
                logger.error(f"❌ Deal creation failed: {result.get('error')}")
                return "ERROR"
                
        except Exception as e:
            logger.error(f"❌ Bitrix error: {e}")
            return "ERROR"
    
    def _create_deal_legal(self, extracted: Dict) -> str:
        """Создание сделки для юрлиц/такелажа в Битрикс"""
        try:
            from chat.ai.function_handlers import handle_create_bitrix_deal_legal
            
            summary_parts = []
            if extracted.get('city'):
                summary_parts.append(f"Город: {extracted['city']}")
            if extracted.get('people'):
                summary_parts.append(f"Грузчики: {extracted['people']}")
            if extracted.get('hours'):
                summary_parts.append(f"Часы: {extracted['hours']}")
            
            if extracted['is_legal_client']:
                summary_parts.append("Юридическое лицо")
            if extracted['needs_tackling']:
                summary_parts.append("Такелаж")
            if extracted.get('hours', 0) > 5:
                summary_parts.append(">5 часов")
            
            result = handle_create_bitrix_deal_legal(
                arguments={
                    'phone': extracted['phone'],
                    'city': extracted.get('city', ''),
                    'hours': extracted.get('hours', 0),
                    'people': extracted.get('people', 0),
                    'summary': ' | '.join(summary_parts)
                },
                context={'chat_id': self.current_chat_id}
            )
            
            if result.get('success'):
                deal_id = result.get('deal_id', 'UNKNOWN')
                logger.info(f"✅ Legal deal created: #{deal_id}")
                return str(deal_id)
            else:
                logger.error(f"❌ Legal deal creation failed: {result.get('error')}")
                return "ERROR"
                
        except Exception as e:
            logger.error(f"❌ Bitrix error: {e}")
            return "ERROR"
    
    def _log(self, chat_id, message, response, extracted, action, response_time_ms, avito_message_model):
        """Логирование в БД"""
        if not avito_message_model:
            return
        
        try:
            chats_log.create_chat_log(
                model=avito_message_model,
                is_success=True,
                answer=response,
                comment=f"Action:{action} | Flags:forbidden={extracted['is_forbidden_service']},tackling={extracted['needs_tackling']}",
                extracted_data=extracted,
                response_time_ms=response_time_ms
            )
            logger.info(f"✅ Logged: {chat_id}")
        except Exception as e:
            logger.error(f"❌ Log failed: {e}")

