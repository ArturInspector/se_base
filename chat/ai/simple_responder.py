"""
Простой автоответчик для Avito
Логика: ключевые слова → legal deal, иначе → минимальная цена
"""
import json
import os
import re
import logging

logger = logging.getLogger(__name__)
LEGAL_KEYWORDS = [
    # Безнал/НДС
    "безнал", "безналичный", "безналичный расчет", "оплатить по безналу", 
    "перевод на расчетный счет", "расчетный счет", "р/с", "рс", "ндс", 
    "оплата с ндс", "без ндс", "с ндс",
    
    # Договоры/документы
    "договор", "заключить договор", "направьте договор", "договор подряда", 
    "договор оказания услуг", "коммерческое предложение", "кп", "счет", 
    "закрывающие документы", "реквизиты", "пакет документов", "печать", "подпись",
    "акт выполненных работ", "просчитайте кп",
    
    # Организации
    "организация", "юрлицо", "юридическое лицо", "компания", "предприятие", 
    "ооо", "ип", "филиал", "офис", "бухгалтерия", "бухгалтер",
    
    # Такелаж/спец работы
    "такелаж", "сейф", "станок", "оборудование", "сервер", "банкомат", 
    "перемещение", "разгрузка фуры", "паллет", "паллеты", "стеллаж", "стеллажи",
    "офисный переезд", "переезд компании", "переезд офиса", "архив", 
    "мебель офисная", "рабочие места", "европаллет", "штабелер",
    
    # Склад/логистика
    "склад", "погрузка", "разгрузка", "фура", "контейнер", "логистика",
    
    # Персонал
    "персонал", "временные работники", "грузчики на постоянку", "на постоянку",
    "на объект", "по договору", "подрядчики", "субподряд", "смена", "вахта",
    
    # Запросы
    "прошу рассчитать", "просьба направить", "требуется", "интересует сотрудничество",
    "уточните условия", "на постоянной основе", "планируем", "требуется на объект",
    "готовы заключить договор", "необходимо с ндс", "нужен акт выполненных работ",
    
    # Объекты
    "объект", "стройка", "производство", "завод", "торговый центр", "офисный центр",
    
    # Тендеры/заявки
    "согласование", "тендер", "заявка", "подряд", "ежемесячно", "по графику",
    "постоянное сотрудничество"
]


class SimpleResponder:
    """Простой автоответчик без сложного AI"""
    
    def __init__(self):
        self._load_pricing()
        logger.info("SimpleResponder инициализирован")
    
    def _load_pricing(self):
        """Загрузка прайсов из JSON"""
        try:
            pricing_path = os.path.join(os.path.dirname(__file__), '../../clean_pricing_data.json')
            with open(pricing_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.pricing = data.get('cities', {})
            logger.info(f"✅ Загружено {len(self.pricing)} городов")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки прайсов: {e}")
            self.pricing = {}
    
    def _has_legal_keywords(self, message: str) -> bool:
        """Проверка на ключевые слова юрлиц/такелажа"""
        message_lower = message.lower()
        
        for keyword in LEGAL_KEYWORDS:
            if keyword in message_lower:
                logger.info(f"Найдено ключевое слово: '{keyword}'")
                return True
        
        return False
    
    def _extract_phone(self, message: str) -> str:
        """Извлечение телефона regex - поддерживает разные форматы"""
        # Паттерны для разных форматов телефонов
        patterns = [
            r'\+?7[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',  # +7(XXX)XXX-XX-XX
            r'8[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',      # 8(XXX)XXX-XX-XX
            r'\d{11}',                                                         # 79991234567
            r'\d{10}',                                                         # 9991234567
        ]
        
        for pattern in patterns:
            phone_match = re.search(pattern, message)
            if phone_match:
                phone = phone_match.group(0)
                # Нормализация: убрать все кроме цифр
                phone_digits = re.sub(r'\D', '', phone)
                
                # Если 10 цифр, добавить 7 в начало
                if len(phone_digits) == 10:
                    phone_digits = '7' + phone_digits
                
                # Если начинается с 8, заменить на 7
                if phone_digits.startswith('8') and len(phone_digits) == 11:
                    phone_digits = '7' + phone_digits[1:]
                
                logger.info(f"📱 Телефон извлечен: {phone_digits}")
                return phone_digits
        
        return ""
    
    def _calculate_min_price(self, city: str) -> tuple:
        """Расчет минимальной цены (2 грузчика × min_hours)"""
        if city not in self.pricing:
            return None, None
        
        city_data = self.pricing[city]
        ppr = city_data.get('ppr', 200)
        min_hours = city_data.get('min_hours', 4.0)
        
        min_price = int(2 * min_hours * ppr)  # 2 грузчика минимум
        
        return min_price, min_hours
    
    def _create_deal_legal(self, phone: str, city: str, message: str, chat_id: str = None) -> str:
        """Создание сделки для юрлиц"""
        try:
            from chat.ai.function_handlers import handle_create_bitrix_deal_legal
            
            result = handle_create_bitrix_deal_legal(
                arguments={
                    'phone': phone,
                    'city': city or 'Не указан',
                    'hours': 0,
                    'people': 0,
                    'summary': f"Юрлицо/Такелаж | Сообщение: {message[:100]}"
                },
                context={'chat_id': chat_id}
            )
            
            if result.get('success'):
                deal_id = result.get('deal_id', 'UNKNOWN')
                logger.info(f"✅ Legal deal created: #{deal_id}")
                return str(deal_id)
            else:
                logger.error(f"❌ Legal deal failed: {result.get('error')}")
                return 'ERROR'
        except Exception as e:
            logger.error(f"❌ Error creating legal deal: {e}")
            return 'ERROR'
    
    def _create_deal_regular(self, phone: str, city: str, message: str, chat_id: str = None) -> str:
        """Создание обычной сделки"""
        try:
            from chat.ai.function_handlers import handle_create_bitrix_deal
            
            result = handle_create_bitrix_deal(
                arguments={
                    'phone': phone,
                    'city': city or 'Не указан',
                    'hours': 0,
                    'people': 0,
                    'summary': f"Автоответчик | Город: {city} | Сообщение: {message[:100]}"
                },
                context={'chat_id': chat_id}
            )
            
            if result.get('success'):
                deal_id = result.get('deal_id', 'UNKNOWN')
                logger.info(f"✅ Regular deal created: #{deal_id}")
                return str(deal_id)
            else:
                logger.error(f"❌ Regular deal failed: {result.get('error')}")
                return 'ERROR'
        except Exception as e:
            logger.error(f"❌ Error creating regular deal: {e}")
            return 'ERROR'
    
    def process(self, message: str, city: str = None, chat_id: str = None) -> str:
        """
        Главная логика автоответчика
        
        Args:
            message: Сообщение клиента
            city: Город из объявления Avito
            chat_id: ID чата
        
        Returns:
            Ответ для клиента
        """
        logger.info(f"🔍 SimpleResponder: message='{message[:50]}...', city={city}")
        
        # Извлечение телефона из любого сообщения
        phone = self._extract_phone(message)
        has_legal_keywords = self._has_legal_keywords(message)
        
        logger.info(f"🔍 Телефон: {'✅ ' + phone if phone else '❌ нет'} | Legal keywords: {'✅' if has_legal_keywords else '❌'}")
        
        # 1. LEGAL KEYWORDS + ТЕЛЕФОН → создать legal deal
        if has_legal_keywords and phone:
            deal_id = self._create_deal_legal(phone, city, message, chat_id)
            if deal_id == 'ERROR':
                return "Произошла ошибка при создании заявки. Пожалуйста, напишите нам позже."
            return f"Отлично! Заявка создана. Наш менеджер свяжется с вами для персонального расчета в течение 15 минут."
        
        # 2. LEGAL KEYWORDS БЕЗ ТЕЛЕФОНА → запросить телефон
        if has_legal_keywords and not phone:
            return "Для персонального расчета оставьте, пожалуйста, номер телефона."
        
        # 3. ТЕЛЕФОН БЕЗ KEYWORDS → создать обычную сделку
        if phone and not has_legal_keywords:
            deal_id = self._create_deal_regular(phone, city or "Не указан", message, chat_id)
            if deal_id == 'ERROR':
                return "Произошла ошибка при создании заявки. Пожалуйста, напишите нам позже или позвоните напрямую по телефону, указанному в объявлении."
            return f"Отлично! Заявка создана. Наш менеджер свяжется с вами в течение 15 минут. Спасибо за обращение!"
        
        # 4. НЕТ ТЕЛЕФОНА И НЕТ KEYWORDS → показать прайс
        # Если нет города → запросить
        if not city:
            return "Подскажите, пожалуйста, в каком городе вам нужны грузчики?"
        
        # Если город не в базе → попросить телефон
        if city not in self.pricing:
            return f"К сожалению, мы пока не работаем в городе {city}. Оставьте номер телефона, и наш менеджер уточнит возможность выполнения заказа."
        
        # Показать прайс города и попросить телефон
        min_price, min_hours = self._calculate_min_price(city)
        
        if min_price:
            return f"Добрый день! Стоимость работы в городе {city}: от {min_price}₽ (минимум 2 грузчика на {int(min_hours)} часа). Оставьте номер телефона для оформления заказа."
        else:
            return "Произошла ошибка при расчете стоимости. Оставьте номер телефона, и наш менеджер свяжется с вами."

