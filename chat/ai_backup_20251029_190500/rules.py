"""
Business Rules - детерминированная бизнес-логика

NO AI - только правила
"""
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class BusinessRules:
    """Бизнес-правила для определения типа клиента и действий"""
    LEGAL_KEYWORDS_EXPLICIT = {
        'юрлиц', 'юридическ', 'счет', 'счёт', 'договор', 
        'инн', 'огрн', 'ооо', 'зао', 'ип'
    }
    
    LEGAL_KEYWORDS_STRONG = {
        'офис', 'компани', 'организац', 'фирм', 'предприят'
    }
    
    LEGAL_KEYWORDS_MODERATE = {
        'склад', 'производств', 'завод', 'цех', 'магазин',
        'регулярн', 'постоянн', 'еженедельн', 'бригада'
    }
    
    LEGAL_KEYWORDS_WEAK = {
        'фура', 'контейнер', 'паллет', 'партия'
    }
    
    PRIVATE_KEYWORDS = {
        'квартир', 'переезд', 'дача', 'дом', 'мебель', 'вещи'
    }
    
    TACKLING_KEYWORDS = {
        'такелаж', 'сейф', 'пианино', 'рояль', 'станок', 'банкомат'
    }
    
    FORBIDDEN_KEYWORDS = {
        'труп', 'умерш', 'покойн', 'похорон', 'морг',
        'мертв', 'усопш', 'скончал', 'погиб', 'тело'
    }
    
    @staticmethod
    def detect_customer_type(extracted: Dict[str, Any]) -> Tuple[str, float]:
        """
        Определить тип клиента: legal, private, unknown
        
        Returns:
            (customer_type, confidence)
        """
        keywords = set([k.lower() for k in extracted.get('keywords', [])])
        people = extracted.get('people')
        hours = extracted.get('hours')
        
        # Явные признаки юрлица
        if keywords & BusinessRules.LEGAL_KEYWORDS_EXPLICIT:
            logger.info(f"✅ Legal entity (explicit keywords): {keywords & BusinessRules.LEGAL_KEYWORDS_EXPLICIT}")
            return 'legal', 1.0
        
        # Сильные признаки юрлица
        if keywords & BusinessRules.LEGAL_KEYWORDS_STRONG:
            logger.info(f"✅ Legal entity (strong keywords): {keywords & BusinessRules.LEGAL_KEYWORDS_STRONG}")
            return 'legal', 0.9
        
        # Большой объем = юрлицо
        if people and people >= 8:
            logger.info(f"✅ Legal entity (large order): {people} people")
            return 'legal', 0.8
        
        # Умеренные признаки юрлица
        if keywords & BusinessRules.LEGAL_KEYWORDS_MODERATE:
            if people and people >= 5:
                return 'legal', 0.8
            return 'legal', 0.6
        
        # Слабые признаки юрлица
        if keywords & BusinessRules.LEGAL_KEYWORDS_WEAK:
            if people and people >= 4:
                return 'legal', 0.7
            return 'unknown', 0.5
        
        # Явные признаки физлица
        if keywords & BusinessRules.PRIVATE_KEYWORDS:
            logger.info(f"✅ Private customer: {keywords & BusinessRules.PRIVATE_KEYWORDS}")
            return 'private', 0.9
        
        # Небольшой заказ = скорее всего физлицо
        if people and people <= 3:
            return 'private', 0.7
        
        # Неизвестно
        return 'unknown', 0.5
    
    @staticmethod
    def check_forbidden(extracted: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Проверить запрещенные услуги
        
        Returns:
            (is_forbidden, reason)
        """
        keywords = set([k.lower() for k in extracted.get('keywords', [])])
        work_description = extracted.get('work_description', '').lower()
        
        # Проверка keywords
        if keywords & BusinessRules.FORBIDDEN_KEYWORDS:
            logger.warning(f"🚨 FORBIDDEN request (keywords): {keywords & BusinessRules.FORBIDDEN_KEYWORDS}")
            return True, 'body_transport'
        
        # Проверка work_description
        for forbidden_word in BusinessRules.FORBIDDEN_KEYWORDS:
            if forbidden_word in work_description:
                logger.warning(f"🚨 FORBIDDEN request (description): '{forbidden_word}' in '{work_description}'")
                return True, 'body_transport'
        
        return False, ''
    
    @staticmethod
    def check_tackling(extracted: Dict[str, Any]) -> bool:
        """Проверить такелажные работы"""
        keywords = set([k.lower() for k in extracted.get('keywords', [])])
        
        if extracted.get('has_special_items'):
            return True
        
        if keywords & BusinessRules.TACKLING_KEYWORDS:
            logger.info(f"⚠️ Tackling work: {keywords & BusinessRules.TACKLING_KEYWORDS}")
            return True
        
        return False
    
    @staticmethod
    def validate_order_params(extracted: Dict[str, Any]) -> Dict[str, str]:
        """
        Валидировать параметры заказа
        
        Returns:
            Dict с ошибками (пусто если все ок)
        """
        issues = {}
        
        people = extracted.get('people')
        hours = extracted.get('hours')
        
        # Минимум 2 грузчика
        if people is not None and people < 2:
            issues['people'] = 'min_2_workers'
        
        # Максимум 20 грузчиков (подозрительно)
        if people is not None and people > 20:
            issues['people'] = 'too_many_workers'
        
        # Минимум 1 час
        if hours is not None and hours < 1:
            issues['hours'] = 'min_1_hour'
        
        # Максимум 24 часа (подозрительно)
        if hours is not None and hours > 24:
            issues['hours'] = 'too_many_hours'
        
        return issues
    
    @staticmethod
    def check_floor_restriction(extracted: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Проверить ограничение по этажу
        
        Правило: этаж > 3 БЕЗ лифта - ОТКАЗ
        
        Returns:
            (is_restricted, reason)
        """
        floor = extracted.get('floor', 0)
        has_elevator = extracted.get('has_elevator', False)
        
        if floor > 3 and not has_elevator:
            logger.warning(f"🚫 Floor restriction: floor {floor} without elevator")
            return True, 'high_floor_no_elevator'
        
        return False, ''
    
    @staticmethod
    def check_heavy_item(extracted: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Проверить тяжелый предмет
        
        Правило: один предмет > 70 кг - такелаж (персональный расчет)
        
        Returns:
            (is_tackling, reason)
        """
        single_item_weight = extracted.get('single_item_weight', 0)
        
        if single_item_weight > 70:
            logger.info(f"⚠️ Heavy item detected: {single_item_weight} kg - tackling required")
            return True, 'heavy_item_tackling'
        
        return False, ''
    
    @staticmethod
    def should_clarify_large_order(extracted: Dict[str, Any], customer_type: str) -> bool:
        """Нужно ли уточнить юрлицо для большого заказа"""
        if customer_type != 'unknown':
            return False
        
        people = extracted.get('people')
        hours = extracted.get('hours')
        
        if (people and people >= 5) or (hours and hours >= 6):
            logger.info(f"⚠️ Large order, need to clarify customer type: {people} people, {hours} hours")
            return True
        
        return False

