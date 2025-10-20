"""
OpenAI Function Calling Definitions

Определения функций которые AI может вызывать для выполнения действий.
Каждая функция должна быть четко описана чтобы AI понимал когда её вызывать.

Принцип: Single Responsibility - каждая функция делает одну вещь.
"""
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


def get_function_definitions() -> List[Dict]:
    """
    Возвращает список определений функций для OpenAI Function Calling
    
    Формат соответствует OpenAI API specification:
    https://platform.openai.com/docs/guides/function-calling
    
    Returns:
        List[Dict]: Список определений функций
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "create_bitrix_deal",
                "description": (
                    "Создать сделку для физического лица в Битрикс24 CRM. "
                    "Используй ТОЛЬКО для обычных клиентов (НЕ для офисов/компаний/юрлиц). "
                    "Вызывай когда клиент указал номер телефона."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone": {
                            "type": "string",
                            "description": "Номер телефона клиента в любом формате"
                        },
                        "city": {
                            "type": "string",
                            "description": "Город где нужны грузчики"
                        },
                        "hours": {
                            "type": "integer",
                            "description": "Количество часов работы"
                        },
                        "people": {
                            "type": "integer",
                            "description": "Количество грузчиков"
                        },
                        "work_type": {
                            "type": "string",
                            "description": "Тип работы (погрузка, переезд, вывоз мусора и т.д.)"
                        },
                        "summary": {
                            "type": "string",
                            "description": "Краткое описание задачи"
                        }
                    },
                    "required": ["phone"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_bitrix_deal_legal",
                "description": (
                    "Создать сделку для юридического лица (компании, офиса) в Битрикс24. "
                    "Используй ТОЛЬКО когда клиент упоминает: офис, компания, юр.лицо, оплата по счету, "
                    "техническое задание, договор, закрывающие документы. "
                    "Вызывай когда клиент указал номер телефона."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone": {
                            "type": "string",
                            "description": "Номер телефона представителя компании"
                        },
                        "company_name": {
                            "type": "string",
                            "description": "Название компании или организации (если указано)"
                        },
                        "city": {
                            "type": "string",
                            "description": "Город где нужны услуги"
                        },
                        "hours": {
                            "type": "integer",
                            "description": "Количество часов работы"
                        },
                        "people": {
                            "type": "integer",
                            "description": "Количество грузчиков"
                        },
                        "work_type": {
                            "type": "string",
                            "description": "Тип работы"
                        },
                        "summary": {
                            "type": "string",
                            "description": "Краткое описание задачи и особенностей (тех.задание, документы и т.д.)"
                        }
                    },
                    "required": ["phone"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_city_pricing",
                "description": (
                    "КРИТИЧЕСКИ ВАЖНО: Получить точные цены для указанного города из прайс-листа. "
                    "ОБЯЗАТЕЛЬНО вызывай эту функцию СРАЗУ как только узнал город клиента! "
                    "Функция вернет точную цену за час, минимальные часы и другие ставки для этого города. "
                    "БЕЗ этих данных ты НЕ МОЖЕШЬ назвать правильную цену!"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "Название города для получения прайса"
                        }
                    },
                    "required": ["city"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_price_estimate",
                "description": (
                    "Рассчитать примерную стоимость услуг грузчиков на основе данных клиента. "
                    "Используй когда клиент спрашивает про цену и предоставил город, часы и количество людей."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "Город для расчета"
                        },
                        "hours": {
                            "type": "integer",
                            "description": "Количество часов работы"
                        },
                        "people": {
                            "type": "integer",
                            "description": "Количество грузчиков"
                        }
                    },
                    "required": ["city", "hours", "people"]
                }
            }
        }
    ]


def get_function_by_name(function_name: str) -> Dict:
    """
    Получить определение функции по имени
    
    Args:
        function_name: Имя функции
        
    Returns:
        Dict: Определение функции или None
    """
    definitions = get_function_definitions()
    for func_def in definitions:
        if func_def["function"]["name"] == function_name:
            return func_def["function"]
    
    logger.warning(f"Функция {function_name} не найдена в определениях")
    return None


def validate_function_arguments(function_name: str, arguments: Dict) -> Tuple[bool, str]:
    """
    Валидация аргументов функции
    
    Args:
        function_name: Имя функции
        arguments: Словарь с аргументами
        
    Returns:
        tuple[bool, str]: (валидны ли аргументы, сообщение об ошибке)
    """
    func_def = get_function_by_name(function_name)
    if not func_def:
        return False, f"Функция {function_name} не существует"
    
    required_params = func_def["parameters"].get("required", [])
    
    for param in required_params:
        if param not in arguments:
            return False, f"Отсутствует обязательный параметр: {param}"
    
    return True, ""

