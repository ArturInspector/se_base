import re
from typing import Dict, Optional
import logging

from .config import HOUR_PATTERNS, PEOPLE_PATTERNS, CITY_URL_PATTERN

logger = logging.getLogger(__name__)


class CityExtractor:
    def __init__(self, pricing_data: dict):
        self.pricing_data = pricing_data
        self.city_mapping = {
            'kyzyl': 'Кызыл',
            'naberezhnye_chelny': 'Набережные Челны',
            'nizhniy_novgorod': 'Нижний Новгород',
            'krasnodar': 'Краснодар',
            'kazan': 'Казань',
            'irkutsk': 'Иркутск',
            'sochi': 'Сочи',
            'cheboksary': 'Чебоксары',
            'izhevsk': 'Ижевск',
            'saratov': 'Саратов',
            'moscow': 'Москва',
            'moskva': 'Москва',
            'sankt-peterburg': 'Санкт-Петербург',
            'sankt_peterburg': 'Санкт-Петербург',
            'saint_petersburg': 'Санкт-Петербург',
            'apatity': 'Апатиты',
            'murmansk': 'Мурманск',
            'petrozavodsk': 'Петрозаводск',
            'arhangelsk': 'Архангельск',
            'severodvinsk': 'Северодвинск',
            'vologda': 'Вологда',
            'cherepovets': 'Череповец',
            'tver': 'Тверь',
            'ryazan': 'Рязань',
            'tula': 'Тула',
            'kaluga': 'Калуга',
            'bryansk': 'Брянск',
            'smolensk': 'Смоленск',
            'kursk': 'Курск',
            'belgorod': 'Белгород',
            'voronezh': 'Воронеж',
            'lipetsk': 'Липецк',
            'tambov': 'Тамбов',
            'penza': 'Пенза',
            'samara': 'Самара',
            'tolyatti': 'Тольятти',
        }
    
    def extract_city_from_url(self, url: str) -> Optional[str]:
        logger.debug(f"Извлечение города из URL: {url}")
        match = re.search(CITY_URL_PATTERN, url)
        if match:
            city_slug = match.group(1)
            logger.debug(f"Извлечен slug города из URL: {city_slug}")
            
            city_name = self.city_mapping.get(city_slug.lower())
            if city_name:
                logger.debug(f"Город из маппинга: {city_name}")
                return city_name
            
            cities = list(self.pricing_data.get('cities', {}).keys())
            for city in cities:
                if city.lower() == city_slug.lower():
                    logger.debug(f"Город найден в прайс-листе: {city}")
                    return city
                if city_slug.lower() in city.lower() or city.lower() in city_slug.lower():
                    logger.debug(f"Город найден (частичное совпадение): {city}")
                    return city
        
        logger.debug("Город из URL не извлечен")
        return None
    
    def extract_city_from_message(self, message: str, ad_data: dict = None) -> Optional[str]:
        logger.debug(f"Извлечение города из сообщения: '{message}', ad_data: {ad_data is not None}")
        message_lower = message.lower()
        
        cities = list(self.pricing_data.get('cities', {}).keys()) if self.pricing_data else []
        
        if ad_data and 'determined_city' in ad_data:
            determined_city = ad_data['determined_city']
            logger.debug(f"Используем уже определенный город: {determined_city}")
            return determined_city
        
        if ad_data and 'city_from_api' in ad_data:
            api_city = ad_data['city_from_api']
            logger.debug(f"Город из API: {api_city}")
            for city in cities:
                if city.lower() == api_city.lower():
                    logger.debug(f"Найден город из API в прайс-листе: {city}")
                    return city
                if city.lower() in api_city.lower() or api_city.lower() in city.lower():
                    logger.debug(f"Найден город из API (частичное совпадение): {city}")
                    return city
        
        if ad_data and 'url' in ad_data:
            url = ad_data['url']
            logger.debug(f"Найден URL в ad_data: {url}")
            city_from_url = self.extract_city_from_url(url)
            if city_from_url:
                logger.debug(f"Извлечен город из URL: {city_from_url}")
                return city_from_url
        
        if ad_data and 'location' in ad_data:
            try:
                ad_location = ad_data.get('location', {})
                ad_city = ad_location.get('city', {}).get('name', '')
                
                if ad_city:
                    logger.debug(f"Город из location: {ad_city}")
                    for city in cities:
                        if city.lower() == ad_city.lower():
                            logger.debug(f"Найден город из location: {ad_city}")
                            return city
                        if city.lower() in ad_city.lower() or ad_city.lower() in city.lower():
                            logger.debug(f"Найден город из location (частичное совпадение): {ad_city}")
                            return city
            except Exception as e:
                logger.debug(f"Ошибка при извлечении города из location: {e}")
        
        for city in cities:
            if city.lower() in message_lower:
                logger.debug(f"Найден город в сообщении: {city}")
                return city
        
        for city in cities:
            city_lower = city.lower()
            if len(city_lower) > 4:
                city_root = city_lower[:-1]
                if city_root in message_lower:
                    logger.debug(f"Найден город в сообщении (частичное совпадение): {city}")
                    return city
        
        logger.debug("Город не найден, возвращаем None")
        return None


class WorkDetailsExtractor:
    def __init__(self, city_extractor: CityExtractor):
        self.city_extractor = city_extractor
    
    def extract_work_details(self, message: str, ad_data: dict = None) -> Dict[str, any]:
        logger.debug(f"Извлечение деталей работы из сообщения: '{message}'")
        message_lower = message.lower()
        
        hours = None
        for pattern in HOUR_PATTERNS:
            match = re.search(pattern, message_lower)
            if match:
                hours = int(match.group(1))
                logger.debug(f"Найдено часов: {hours}")
                break
        
        people = None
        for pattern in PEOPLE_PATTERNS:
            match = re.search(pattern, message_lower)
            if match:
                people = int(match.group(1))
                logger.debug(f"Найдено людей: {people}")
                break
        
        city = self.city_extractor.extract_city_from_message(message, ad_data)
        logger.debug(f"Извлеченный город: '{city}'")
        
        if city is None:
            logger.debug("Город не найден, устанавливаем флаг UNKNOWN_CITY")
            city = "UNKNOWN_CITY"
        
        return {
            'hours': hours,
            'people': people,
            'city': city
        }

