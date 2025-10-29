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
            "description": "TRUE если юрлицо: офис, склад, магазин, овощебаза, регулярно, >4 грузчиков, счет, договор"
        }
    },
    "required": ["city", "people", "hours", "phone", "floor", "has_elevator", 
                 "single_item_weight", "is_greeting", "is_forbidden_service", "needs_tackling", "is_legal_client"],
    "additionalProperties": False
}

EXTRACTION_PROMPT = """Извлеки данные из сообщения клиента службы грузчиков.

ВАЖНО - ФЛАГИ:
- is_forbidden_service: TRUE если клиент просит перенести ЧЕЛОВЕКА (деда, старика, бабушку, больного, покойника, инвалида)
- needs_tackling: TRUE если сейф/пианино/рояль/станок/банкомат ИЛИ вес одного предмета >70кг
- is_legal_client: TRUE если юрлицо (офис, склад, магазин, счет, договор, регулярно, >4 грузчиков, смена)

Примеры:
"Нужно вынести старика с 5 этажа" → is_forbidden_service: true
"Поднять сейф на 3 этаж" → needs_tackling: true
"Грузчики для офиса, нужен счет" → is_legal_client: true
"""


AI_DISCLAIMER = "💬 Я AI-бот SE Express. "

TEMPLATES = {
    "greeting": "Здравствуйте! Чем могу помочь?",
    
    "forbidden": "Извините, мы не оказываем услуги по переносу людей.",
    
    "floor_restriction": "Извините, мы работаем только до 3 этажа без лифта.",
    
    "tackling_ask_phone": "Для перемещения тяжелых предметов (сейф, пианино) требуется такелаж. Оставьте номер телефона, и мы рассчитаем стоимость.",
    
    "legal_ask_phone": "Для юридических лиц предоставляем счет и договор. Оставьте номер телефона менеджера.",
    
    "ask_city": "В каком городе вам нужны грузчики?",
    
    "ask_details": "Сколько грузчиков и на сколько часов нужно в {city}?",
    
    "show_price": "Стоимость работы в {city}: {price}₽ ({people} грузчиков × {hours}ч). Оставьте номер телефона для оформления заказа.",
    
    "deal_created": "Заявка #{deal_id} создана! Наш менеджер свяжется с вами в течение 15 минут.",
    
    "error": "Произошла ошибка. Пожалуйста, оставьте номер телефона, и мы вам перезвоним."
}


PRICING = {
    "Москва": {"ppr": 300, "min_hours": 3},
    "Санкт-Петербург": {"ppr": 250, "min_hours": 3},
    "default": {"ppr": 200, "min_hours": 4}
}


class SimpleAIProcessorV2:
    """Упрощенный процессор: 1 AI вызов → if-else → шаблон"""
    
    def __init__(self):
        logger.info("SimpleAIProcessorV2: Инициализация")
        self._init_openai()
    
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
    
    def process(self, message: str, chat_id: str = None, avito_message_model=None) -> str:
        """
        Главный метод: сообщение → ответ
        """
        start_time = time.time()
        
        try:
            extracted = self._extract_data(message, chat_id)
            response, action = self._apply_rules(extracted)
            
            # Добавить disclaimer если первое сообщение
            is_first_message = self._is_first_message(chat_id)
            if is_first_message:
                response = AI_DISCLAIMER + response
            
            response_time_ms = int((time.time() - start_time) * 1000)
            self._log(chat_id, message, response, extracted, action, response_time_ms, avito_message_model)
            
            logger.info(f"✅ Response: {action} | First:{is_first_message} | {response_time_ms}ms")
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
    
    def _extract_data(self, message: str, chat_id: str = None) -> Dict[str, Any]:
        """
        AI извлечение: сообщение → JSON с флагами
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
            
            messages = context + [
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
        """Fallback если AI недоступен"""
        return {
            "city": "",
            "people": 0,
            "hours": 0,
            "phone": "",
            "floor": 0,
            "has_elevator": False,
            "single_item_weight": 0,
            "is_greeting": False,
            "is_forbidden_service": False,
            "needs_tackling": False,
            "is_legal_client": False
        }
    
    def _apply_rules(self, extracted: Dict) -> Tuple[str, str]:
        """
        IF-ELSE по ФЛАГАМ (NO AI!)
        
        Returns:
            (response_text, action_name)
        """
        
        # ПРИВЕТСТВИЕ (если только поздоровался, без данных)
        if extracted['is_greeting'] and not extracted['city'] and not extracted['people']:
            return (TEMPLATES["greeting"], "greeting")
        
        if extracted['is_forbidden_service']:
            return (TEMPLATES["forbidden"], "forbidden")
        
        if extracted['floor'] > 3 and not extracted['has_elevator']:
            return (TEMPLATES["floor_restriction"], "floor_restriction")
        if extracted['needs_tackling']:
            if not extracted['phone']:
                return (TEMPLATES["tackling_ask_phone"], "tackling_ask_phone")
            else:
                deal_id = self._create_deal(extracted, is_tackling=True)
                return (TEMPLATES["deal_created"].format(deal_id=deal_id), "tackling_deal_created")
        
        if extracted['is_legal_client']:
            if not extracted['phone']:
                return (TEMPLATES["legal_ask_phone"], "legal_ask_phone")
            else:
                deal_id = self._create_deal(extracted, is_legal=True)
                return (TEMPLATES["deal_created"].format(deal_id=deal_id), "legal_deal_created")
        
        # СБОР ДАННЫХ #1: Город
        if not extracted['city']:
            return (TEMPLATES["ask_city"], "ask_city")
        
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
    
    def _calculate_price(self, extracted: Dict) -> int:
        """Расчет цены"""
        city = extracted['city']
        people = extracted['people']
        hours = extracted['hours']
        
        pricing = PRICING.get(city, PRICING["default"])
        ppr = pricing['ppr']
        min_hours = pricing['min_hours']
        hours_charged = max(hours, min_hours)
        
        return people * hours_charged * ppr
    
    def _create_deal(self, extracted: Dict, is_tackling: bool = False, is_legal: bool = False) -> str:
        """Создание сделки в Битрикс"""
        try:
            from chat.ai.function_handlers import handle_create_bitrix_deal, handle_create_bitrix_deal_legal
            
            if is_legal:
                result = handle_create_bitrix_deal_legal(
                    arguments={
                        'phone': extracted['phone'],
                        'city': extracted['city'],
                        'hours': extracted['hours'],
                        'people': extracted['people']
                    },
                    context={}
                )
            else:
                price = self._calculate_price(extracted)
                result = handle_create_bitrix_deal(
                    arguments={
                        'phone': extracted['phone'],
                        'city': extracted['city'],
                        'hours': extracted['hours'],
                        'people': extracted['people'],
                        'price': price,
                        'summary': f"Такелаж: {extracted['single_item_weight']}кг" if is_tackling else "",
                        'floor': extracted['floor'],
                        'has_elevator': extracted['has_elevator']
                    },
                    context={}
                )
            
            if result.get('success'):
                deal_id = result.get('deal_id', '???')
                logger.info(f"✅ Deal created: #{deal_id}")
                return str(deal_id)
            else:
                logger.error(f"❌ Deal creation failed: {result.get('error')}")
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

