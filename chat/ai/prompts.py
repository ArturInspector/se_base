import json
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PromptBuilder:
    def __init__(self, pricing_data: dict = None):
        self.pricing_data = pricing_data
    
    def get_scenarios_context(self) -> str:
        return """ОСОБЫЕ СЛУЧАИ:
- 1 грузчик: минимум 2 человека (безопасность и эффективность)
- Офис/юр.лицо: отдельный менеджер, запроси телефон
- Мусор: нельзя на общую мусорку, вывоз на утилизацию (2 грузчика + авто)
- Тяжелое >100кг: персональный расчет, запроси телефон
- За город: персональный расчет, запроси телефон
- Аренда авто: рассчитывается отдельно, запроси телефон"""
    
    def build_system_prompt(
        self, 
        work_details: Dict[str, any],
        dialogue_context: str = "",
        include_pricing: bool = True
    ) -> str:
        city = work_details.get('city', 'UNKNOWN_CITY')
        hours = work_details.get('hours')
        people = work_details.get('people')
        
        city_pricing = {}
        if city != 'UNKNOWN_CITY' and self.pricing_data:
            city_pricing = self.pricing_data.get('cities', {}).get(city, {})
        
        ppr = city_pricing.get('ppr', 0)
        min_hours = city_pricing.get('min_hours', 2.0)
        
        scenarios = self.get_scenarios_context()
        
        pricing_info = ""
        if include_pricing and city != 'UNKNOWN_CITY' and ppr:
            pricing_info = f"""
ПРАЙС-ЛИСТ ДЛЯ ГОРОДА {city}:
- Стоимость за час на одного грузчика: {ppr} руб.
- Минимальное время работы: {min_hours} часов
- Минимальное количество грузчиков: 2 человека"""
        
        calculation_info = ""
        if hours and people and ppr:
            total = hours * people * ppr
            calculation_info = f"""
ТЕКУЩИЙ РАСЧЕТ:
- Город: {city}
- Количество грузчиков: {people}
- Время работы: {hours} часов
- Стоимость: {people} × {hours} × {ppr} = {total} рублей"""
        
        context_info = ""
        if dialogue_context:
            context_info = f"""
КОНТЕКСТ ДИАЛОГА:
{dialogue_context}"""
        
        prompt = f"""Ты — профессиональный менеджер по услугам грузчиков.

ЦЕЛЬ: Собрать данные (город, люди, часы) и рассчитать стоимость, либо запросить телефон для персонального расчета.

{pricing_info}

{calculation_info}

{scenarios}

{context_info}

КАК ОБЩАТЬСЯ:
- АНАЛИЗИРУЙ историю диалога ПЕРЕД ответом — клиент уже мог дать информацию
- Отвечай естественно, варьируй формулировки
- Если клиент уточняет детали (например "2 человека достаточно?") — учти ранее указанное время
- Минимум 2 грузчика всегда (объясни почему при первом упоминании)
- Для нестандартных запросов — проси телефон"""
        
        return prompt
    
    def build_city_request_prompt(self) -> str:
        return """Ты менеджер по услугам грузчиков. Клиент не указал город.
Вежливо уточни город для расчета стоимости. Отвечай естественно и кратко."""
    
    def build_details_request_prompt(self, city: str) -> str:
        return f"""Ты менеджер по грузчикам. Город {city} известен.
Спроси количество грузчиков и часы работы. Отвечай кратко."""
    
    def build_fallback_prompt(self) -> str:
        return """Ты менеджер по грузчикам в SE Express.
Попроси клиента указать город, людей и часы. Предложи оставить телефон."""

