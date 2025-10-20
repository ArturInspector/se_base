import json
import os
from typing import Dict, Optional
import logging

from .config import PRICING_DATA_PATH
import cities.api

logger = logging.getLogger(__name__)


class PricingCalculator:
    DEFAULT_PRICING = {
        'ppr': 700,              # Грузчики руб/час
        'min_hours': 2.0,        # Минимум часов для грузчиков
        'shift_8h': 580,         # Аутсорсинг 8 часов руб/час
        'shift_12h': 500,        # Аутсорсинг 12 часов руб/час
        'gazelle': 2000,         # Газель руб/час
        'gazelle_min_hours': 2.0,# Минимум часов для Газели
        'nds_5': 2200
    }
    
    def __init__(self, pricing_data_path: str = None):
        if pricing_data_path is None:
            pricing_data_path = PRICING_DATA_PATH
        
        try:
            with open(pricing_data_path, 'r', encoding='utf-8') as f:
                self.pricing_data = json.load(f)
            logger.info(f"Прайс-лист загружен из {pricing_data_path}")
        except Exception as e:
            logger.warning(f"Не удалось загрузить прайс-лист: {e}")
            self.pricing_data = None
    
    def get_city_pricing(self, city: str) -> Optional[Dict]:
        if not self.pricing_data:
            return None
        
        return self.pricing_data.get('cities', {}).get(city)
    
    def calculate_price(self, work_details: Dict[str, any]) -> Optional[str]:
        city = work_details['city']
        hours = work_details['hours']
        people = work_details['people']
        
        logger.debug(f"Расчет стоимости: city={city}, hours={hours}, people={people}")
        
        if not self.pricing_data:
            logger.debug("pricing_data отсутствует")
            return None
        
        if not hours or not people:
            logger.debug(f"hours={hours} или people={people} отсутствуют")
            return None
        
        if city == "UNKNOWN_CITY":
            logger.debug("Город неизвестен, возвращаем запрос города")
            return "CITY_REQUEST"
        
        city_data = self.pricing_data['cities'].get(city)
        
        if not city_data:
            logger.debug(f"Город {city} не найден в индивидуальном прайс-листе")
            
            if not cities.api.is_city_supported(city):
                logger.warning(f"Город {city} не найден в БД поддерживаемых городов")
                return "Извините, но мы пока не работаем в этом городе. Мы предоставляем услуги в 1120+ городах России. Пожалуйста, уточните название города."
            
            logger.info(f"Используем дефолтные ставки для города {city}")
            city_data = self.DEFAULT_PRICING
        
        ppr = city_data.get('ppr')
        min_hours = city_data.get('min_hours', 2.0)
        
        logger.debug(f"Для города {city}: min_hours={min_hours}, ppr={ppr}")
        
        if not ppr:
            logger.debug(f"ppr отсутствует для города {city}")
            return None
        
        if hours < min_hours:
            logger.debug(f"{hours} < {min_hours}, возвращаем сообщение о минималке")
            return f"Минимальное время заказа в городе {city} составляет {min_hours} часов. Для расчета стоимости укажите, пожалуйста, количество часов не менее {min_hours}."
        
        total_price = people * hours * ppr
        logger.debug(f"Расчет: {people} × {hours} × {ppr} = {total_price}")
        
        return f"Стоимость составит {total_price} рублей"

