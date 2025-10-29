"""
OpenAI Structured Output Schemas

ONE AI CALL извлекает ВСЕ данные
Strict JSON mode - no hallucinations
"""

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": [
                "greeting",           # Приветствие
                "ask_price",          # Спрашивает цену
                "order_movers",       # Хочет заказать
                "provide_phone",      # Дает телефон
                "clarification",      # Уточняющий вопрос
                "complaint",          # Жалоба
                "off_topic"           # Не по теме
            ],
            "description": "Намерение клиента"
        },
        "city": {
            "type": "string",
            "description": "Название города (empty string если не указан)"
        },
        "people": {
            "type": "integer",
            "description": "Количество грузчиков (0 если не указано)"
        },
        "hours": {
            "type": "number",
            "description": "Количество часов (0 если не указано)"
        },
        "phone": {
            "type": "string",
            "description": "Номер телефона в любом формате (empty string если нет)"
        },
        "keywords": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Ключевые слова из сообщения: юрлицо, офис, счет, договор, компания, такелаж, сейф, пианино, квартира, переезд, etc"
        },
        "work_description": {
            "type": "string",
            "description": "Краткое описание работы от клиента (empty string если нет)"
        },
        "has_special_items": {
            "type": "boolean",
            "description": "Есть ли тяжелые предметы (сейф, пианино, станок)?"
        },
        "single_item_weight": {
            "type": "integer",
            "description": "Вес ОДНОГО предмета в кг (0 если не указан). Если >70 кг - это такелаж!"
        },
        "floor": {
            "type": "integer",
            "description": "Этаж (0 если не указан)"
        },
        "has_elevator": {
            "type": "boolean",
            "description": "Есть ли лифт (false если не указано)"
        },
        "urgency": {
            "type": "string",
            "enum": ["urgent", "today", "tomorrow", "later", "unknown"],
            "description": "Срочность заказа"
        },
        "is_forbidden_service": {
            "type": "boolean",
            "description": "TRUE если запрос на перенос/вынос ЛЮДЕЙ (живых, мертвых, больных, пожилых, инвалидов). Мы НЕ переносим людей!"
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Уверенность в извлеченных данных (0.0-1.0)"
        }
    },
    "required": [
        "intent",
        "city",
        "people",
        "hours",
        "phone",
        "keywords",
        "work_description",
        "has_special_items",
        "single_item_weight",
        "floor",
        "has_elevator",
        "urgency",
        "is_forbidden_service",
        "confidence"
    ],
    "additionalProperties": False
}


EXTRACTION_PROMPT = """Ты - эксперт по извлечению структурированных данных из запросов клиентов службы грузчиков.

Твоя задача: извлечь ВСЕ данные из сообщения клиента в строгом JSON формате.

ВАЖНЫЕ ПРАВИЛА:
1. Город: точное название (Москва, Санкт-Петербург, Казань, etc). Если нет - empty string ""
2. Телефон: любой формат (89001234567, +7 900 123-45-67, 8-900-123-45-67). Если нет - empty string ""
3. Keywords: ВСЕ важные слова (юрлицо, офис, счет, договор, компания, квартира, такелаж, сейф, пианино)
4. Числа (people, hours, floor, single_item_weight): если не указано - 0
5. single_item_weight: вес ОДНОГО предмета в кг. Если >70кг - это такелаж!
6. Boolean (has_elevator, has_special_items, is_forbidden_service): если не указано - false
7. Intent:
   - greeting: если просто приветствие
   - ask_price: спрашивает сколько стоит
   - order_movers: готов заказать
   - provide_phone: дает телефон
   - clarification: уточняющий вопрос
8. has_special_items: true если упомянуты сейф, пианино, рояль, станок, банкомат
9. floor и has_elevator: ⚠️ ВАЖНО! Если этаж > 3 БЕЗ лифта - мы НЕ работаем!
10. ⚠️ is_forbidden_service: TRUE если запрос на ПЕРЕНОС/ВЫНОС ЛЮДЕЙ (деда, бабушку, человека, больного, покойника, тела, инвалида). МЫ НЕ ОКАЗЫВАЕМ такие услуги!
11. Confidence: 0.0-1.0 насколько уверен в извлеченных данных

ПРИМЕРЫ:

Сообщение: "Привет, сколько стоит грузчик в Москве?"
→ {"intent": "ask_price", "city": "Москва", "people": 0, "hours": 0, "phone": "", "keywords": ["москва"], "work_description": "", "has_special_items": false, "single_item_weight": 0, "floor": 0, "has_elevator": false, "urgency": "unknown", "is_forbidden_service": false, "confidence": 0.9}

Сообщение: "Нужны грузчики для офиса, счет нужен, 8 человек"
→ {"intent": "order_movers", "city": "", "people": 8, "hours": 0, "phone": "", "keywords": ["офис", "счет"], "work_description": "для офиса", "has_special_items": false, "single_item_weight": 0, "floor": 0, "has_elevator": false, "urgency": "unknown", "is_forbidden_service": false, "confidence": 0.8}

Сообщение: "надо деда с 5 этажа вынести"
→ {"intent": "order_movers", "city": "", "people": 0, "hours": 0, "phone": "", "keywords": [], "work_description": "надо деда с 5 этажа вынести", "has_special_items": false, "single_item_weight": 0, "floor": 5, "has_elevator": false, "urgency": "unknown", "is_forbidden_service": true, "confidence": 0.95}

Сообщение: "Нужно поднять сейф 120 кг на 7 этаж, лифта нет"
→ {"intent": "order_movers", "city": "", "people": 0, "hours": 0, "phone": "", "keywords": ["сейф"], "work_description": "поднять сейф 120 кг на 7 этаж", "has_special_items": true, "single_item_weight": 120, "floor": 7, "has_elevator": false, "urgency": "unknown", "is_forbidden_service": false, "confidence": 0.9}

Сообщение: "Помочь с переездом на 5 этаж, лифт есть"
→ {"intent": "order_movers", "city": "", "people": 0, "hours": 0, "phone": "", "keywords": ["переезд"], "work_description": "переезд на 5 этаж", "has_special_items": false, "single_item_weight": 0, "floor": 5, "has_elevator": true, "urgency": "unknown", "is_forbidden_service": false, "confidence": 0.9}

Сообщение: "Нужен один грузчик"
→ {"intent": "order_movers", "city": "", "people": 1, "hours": 0, "phone": "", "keywords": [], "work_description": "один грузчик", "has_special_items": false, "single_item_weight": 0, "floor": 0, "has_elevator": false, "urgency": "unknown", "is_forbidden_service": false, "confidence": 0.9}

Извлеки данные из следующего сообщения:"""

