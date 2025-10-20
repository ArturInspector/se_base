"""
Function Handlers для OpenAI Function Calling

Обработчики которые выполняют реальные действия когда AI вызывает функции.
Каждый handler должен быть идемпотентным и безопасным.

"""
import json
import logging
from typing import Dict, Any, Optional
import traceback
import recalls.bitrix
import utils

logger = logging.getLogger(__name__)


def handle_create_bitrix_deal(arguments: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Обработчик создания сделки в Битриксе
    
    Args:
        arguments: Аргументы от AI (phone, city, hours, people, etc.)
        context: Контекст выполнения (chat_id, user_id, ad_data)
        
    Returns:
        Dict: Результат выполнения {"success": bool, "deal_id": int, "message": str}
    """
    try:

        
        phone = arguments.get("phone")
        if not phone:
            return {
                "success": False,
                "error": "Отсутствует номер телефона",
                "message": "Не могу создать сделку без номера телефона"
            }
        
        normalized_phone = utils.telephone(phone)
        if not normalized_phone:
            return {
                "success": False,
                "error": "Некорректный номер телефона",
                "message": f"Номер телефона {phone} не прошел валидацию"
            }
        
        city = arguments.get("city", "Не указан")
        hours = arguments.get("hours", "")
        people = arguments.get("people", "")
        work_type = arguments.get("work_type", "")
        summary = arguments.get("summary", "")
        
        source_parts = []
        if city:
            source_parts.append(f"Город: {city}")
        if hours:
            source_parts.append(f"Часов: {hours}")
        if people:
            source_parts.append(f"Грузчиков: {people}")
        if work_type:
            source_parts.append(f"Тип работы: {work_type}")
        if summary:
            source_parts.append(f"Описание: {summary}")
        
        source_description = " | ".join(source_parts) if source_parts else "Avito заявка"
        
        chat_id = context.get("chat_id") if context else None
        if chat_id:
            import chats_log
            try:
                dialogue_summary = chats_log.api.get_chat_summary(chat_id, max_messages=5)
                if dialogue_summary:
                    source_description = f"{source_description} | История: {dialogue_summary}"
            except Exception as e:
                logger.warning(f"Не удалось получить историю диалога: {e}")
        
        logger.info(f"Создание сделки в Битриксе: телефон={normalized_phone}, описание={source_description[:100]}")
        
        deal_result = recalls.bitrix.create_deal_from_avito(
            phone=normalized_phone,
            username="AvitoUser",
            source_description=source_description
        )
        
        if deal_result:
            deal_id = deal_result if isinstance(deal_result, int) else "создана"
            logger.info(f"Сделка успешно создана: {deal_id}")
            return {
                "success": True,
                "deal_id": deal_id,
                "phone": normalized_phone,
                "message": f"Сделка #{deal_id} успешно создана в Битрикс24"
            }
        else:
            logger.error("Битрикс вернул пустой результат")
            return {
                "success": False,
                "error": "Empty result from Bitrix",
                "message": "Не удалось создать сделку, попробуйте позже"
            }
            
    except Exception as e:
        logger.error(f"Ошибка создания сделки в Битриксе: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "message": "Произошла ошибка при создании сделки"
        }


def handle_calculate_price_estimate(arguments: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Обработчик расчета стоимости
    
    Args:
        arguments: Аргументы от AI (city, hours, people)
        context: Контекст выполнения
        
    Returns:
        Dict: Результат расчета {"success": bool, "price_info": str}
    """
    try:
        from .pricing import PricingCalculator
        
        city = arguments.get("city")
        hours = arguments.get("hours")
        people = arguments.get("people")
        
        if not all([city, hours, people]):
            return {
                "success": False,
                "error": "Недостаточно данных для расчета",
                "message": "Нужен город, количество часов и грузчиков"
            }
        
        calculator = PricingCalculator()
        
        work_details = {
            "city": city,
            "hours": hours,
            "people": people
        }
        
        price_info = calculator.calculate_price(work_details)
        
        if price_info and price_info != "CITY_REQUEST":
            logger.info(f"Расчет выполнен: {city}, {hours}ч, {people}чел = {price_info[:50]}")
            return {
                "success": True,
                "price_info": price_info,
                "message": price_info
            }
        else:
            return {
                "success": False,
                "error": "Не удалось рассчитать стоимость",
                "message": f"Нет прайс-листа для города {city}"
            }
            
    except Exception as e:
        logger.error(f"Ошибка расчета стоимости: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "message": "Произошла ошибка при расчете стоимости"
        }


def handle_get_city_pricing(arguments: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Обработчик получения прайса для города
    
    Args:
        arguments: Аргументы от AI (city)
        context: Контекст выполнения
        
    Returns:
        Dict: Прайс для города {"success": bool, "city": str, "ppr": int, ...}
    """
    try:
        from .pricing import PricingCalculator
        import cities.api
        
        city = arguments.get("city")
        if not city:
            return {
                "success": False,
                "error": "Не указан город",
                "message": "Необходимо указать название города"
            }
        
        calculator = PricingCalculator()
        city_pricing = calculator.get_city_pricing(city)
        
        if city_pricing:
            logger.info(f"Найден прайс для города {city}: ppr={city_pricing.get('ppr')}")
            return {
                "success": True,
                "city": city,
                "ppr": city_pricing.get("ppr"),
                "min_hours": city_pricing.get("min_hours", 2.0),
                "shift_8h": city_pricing.get("shift_8h"),
                "shift_12h": city_pricing.get("shift_12h"),
                "gazelle": city_pricing.get("gazelle", 2000),
                "message": (
                    f"Прайс для {city}: {city_pricing.get('ppr')}₽/час, "
                    f"минимум {city_pricing.get('min_hours', 2.0)} часа"
                )
            }
        else:
            is_supported = cities.api.is_city_supported(city)
            
            if is_supported:
                logger.info(f"Город {city} в базе, используем стандартные цены")
                return {
                    "success": True,
                    "city": city,
                    "ppr": 700,
                    "min_hours": 2.0,
                    "shift_8h": 580,
                    "shift_12h": 500,
                    "gazelle": 2000,
                    "message": f"Прайс для {city}: 700₽/час (стандартная ставка), минимум 2 часа"
                }
            else:
                logger.warning(f"Город {city} не найден в базе")
                return {
                    "success": False,
                    "error": "Город не найден",
                    "city": city,
                    "message": (
                        f"Город {city} не найден в базе. "
                        f"Мы работаем в 1000+ городах России. "
                        f"Уточните, пожалуйста, правильное название города."
                    )
                }
            
    except Exception as e:
        logger.error(f"Ошибка получения прайса для города: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "message": "Ошибка при получении прайс-листа"
        }


def handle_create_bitrix_deal_legal(arguments: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Обработчик создания сделки для юридического лица
    """
    try:
        phone = arguments.get("phone")
        if not phone:
            return {
                "success": False,
                "error": "Отсутствует номер телефона",
                "message": "Не могу создать сделку без номера телефона"
            }
        
        normalized_phone = utils.telephone(phone)
        if not normalized_phone:
            return {
                "success": False,
                "error": "Некорректный номер телефона",
                "message": f"Номер {phone} не прошел валидацию"
            }
        
        company_name = arguments.get("company_name")
        city = arguments.get("city", "Не указан")
        hours = arguments.get("hours", "")
        people = arguments.get("people", "")
        work_type = arguments.get("work_type", "")
        summary = arguments.get("summary", "")
        
        source_parts = ["ЮР.ЛИЦО"]
        if city:
            source_parts.append(f"Город: {city}")
        if hours:
            source_parts.append(f"Часов: {hours}")
        if people:
            source_parts.append(f"Грузчиков: {people}")
        if work_type:
            source_parts.append(f"Тип: {work_type}")
        if summary:
            source_parts.append(f"Описание: {summary}")
        
        source_description = " | ".join(source_parts)
        
        chat_id = context.get("chat_id") if context else None
        if chat_id:
            import chats_log
            try:
                dialogue_summary = chats_log.api.get_chat_summary(chat_id, max_messages=5)
                if dialogue_summary:
                    source_description = f"{source_description} | История: {dialogue_summary}"
            except Exception as e:
                logger.warning(f"Не удалось получить историю: {e}")
        
        logger.info(f"Создание сделки ЮРЛИЦА: {normalized_phone}, компания={company_name}")
        
        deal_result = recalls.bitrix.create_deal_from_avito_legal(
            phone=normalized_phone,
            username="AvitoUser",
            source_description=source_description,
            company_name=company_name
        )
        
        if deal_result:
            deal_id = deal_result if isinstance(deal_result, int) else "создана"
            logger.info(f"Сделка юрлица создана: {deal_id}")
            return {
                "success": True,
                "deal_id": deal_id,
                "phone": normalized_phone,
                "company_name": company_name,
                "message": "Сделка для юридического лица успешно создана"
            }
        else:
            logger.error("Битрикс вернул пустой результат")
            return {
                "success": False,
                "error": "Empty result from Bitrix",
                "message": "Не удалось создать сделку"
            }
            
    except Exception as e:
        logger.error(f"Ошибка создания сделки юрлица: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "message": "Ошибка при создании сделки"
        }


FUNCTION_HANDLERS = {
    "get_city_pricing": handle_get_city_pricing,
    "create_bitrix_deal": handle_create_bitrix_deal,
    "create_bitrix_deal_legal": handle_create_bitrix_deal_legal,
    "calculate_price_estimate": handle_calculate_price_estimate,
}


def execute_function(function_name: str, arguments: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Роутер для выполнения функций
    
    Args:
        function_name: Имя функции которую вызвал AI
        arguments: Аргументы от AI
        context: Контекст выполнения (chat_id, user_id, ad_data)
        
    Returns:
        Dict: Результат выполнения функции
    """
    logger.info(f"Выполнение функции: {function_name}")
    logger.debug(f"Аргументы: {json.dumps(arguments, ensure_ascii=False)}")
    
    if function_name not in FUNCTION_HANDLERS:
        error_msg = f"Функция {function_name} не имеет обработчика"
        logger.error(error_msg)
        return {
            "success": False,
            "error": "Unknown function",
            "message": error_msg
        }
    
    handler = FUNCTION_HANDLERS[function_name]
    
    try:
        result = handler(arguments, context)
        logger.debug(f"Результат выполнения: {json.dumps(result, ensure_ascii=False)[:200]}")
        return result
    except Exception as e:
        logger.error(f"Критическая ошибка в execute_function: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "message": "Внутренняя ошибка при выполнении функции"
        }


def format_function_result_for_ai(result: Dict[str, Any]) -> str:
    """
    Форматирование результата функции для отправки обратно в AI
    
    AI получит этот текст и сгенерирует ответ клиенту на его основе
    
    Args:
        result: Результат выполнения функции
        
    Returns:
        str: Отформатированный текст для AI
    """
    if result.get("success"):
        return json.dumps({
            "status": "success",
            "data": {k: v for k, v in result.items() if k != "success"}
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "error",
            "error": result.get("error", "Unknown error"),
            "message": result.get("message", "")
        }, ensure_ascii=False)

