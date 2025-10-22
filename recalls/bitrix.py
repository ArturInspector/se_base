from fast_bitrix24 import Bitrix
import config
import utils

bitrix = Bitrix(config.Production.BITRIX_WEBHOOK)

# Опциональная инициализация chatbot битрикса
try:
    if hasattr(config.Production, 'chatbot_bitrix_webhook') and config.Production.chatbot_bitrix_webhook:
        chat_bitrix = Bitrix(config.Production.chatbot_bitrix_webhook)
    else:
        chat_bitrix = None
except Exception:
    chat_bitrix = None


def _normalize_phone_for_bitrix(phone: str) -> str:
    """
    Централизованная нормализация телефона для Битрикса
    
    Args:
        phone: номер телефона в любом формате
    
    Returns:
        10-значный номер без кода страны (для совместимости с Битриксом)
    """
    normalized = utils.telephone(phone)
    if normalized is None:
        normalized = phone
    return normalized


def update_source_description(deal_id, source_description):
    params = {
        'id': deal_id,
        'fields': {
            'SOURCE_DESCRIPTION': source_description,
        }
    }

    data = bitrix.call('crm.deal.update', params)
    return data


def create_deal_from_avito(phone, username, source_description):
    """
    Создание сделки для физических лиц из Авито
    
    Returns:
        int: ID созданной сделки в Битриксе
    """
    normalized_phone = _normalize_phone_for_bitrix(phone)
    contact_id = find_or_create_contact(phone, username)
    
    if not contact_id:
        raise Exception("Не удалось создать/найти контакт")
    
    params = {
        'fields': {
            'TITLE': '+7{} - Авито сообщения'.format(normalized_phone),
            'TYPE_ID': 'SALE',
            'STAGE_ID': 'C4:NEW',
            'SOURCE_ID': 'AvitoMessanger',
            'SOURCE_DESCRIPTION': source_description,
            'CATEGORY_ID': '4',
            'CONTACT_ID': contact_id,
            'ASSIGNED_BY_ID': '116',
        }
    }

    # crm.deal.add возвращает ID сделки напрямую
    deal_id = bitrix.call('crm.deal.add', params)
    return int(deal_id) if deal_id else None


def create_deal_from_avito_legal(phone, username, source_description, company_name=None):
    """
    Создание сделки для юридических лиц из Авито
    
    Returns:
        int: ID созданной сделки в Битриксе
    """
    normalized_phone = _normalize_phone_for_bitrix(phone)
    contact_id = find_or_create_contact(phone, username)
    
    if not contact_id:
        raise Exception("Не удалось создать/найти контакт")
    
    title = '+7{} - Авито (Юр.лицо)'.format(normalized_phone)
    if company_name:
        title = '+7{} - {} (Юр.лицо)'.format(normalized_phone, company_name)
    
    if company_name:
        source_description = f"Компания: {company_name} | {source_description}"
    
    params = {
        'fields': {
            'TITLE': title,
            'TYPE_ID': 'SALE',
            'STAGE_ID': 'C4:NEW',
            'SOURCE_ID': 'AvitoMessanger',
            'SOURCE_DESCRIPTION': source_description,
            'CATEGORY_ID': '46',
            'CONTACT_ID': contact_id,
            'ASSIGNED_BY_ID': '116',
        }
    }

    # crm.deal.add возвращает ID сделки напрямую
    deal_id = bitrix.call('crm.deal.add', params)
    return int(deal_id) if deal_id else None


def create_deal_from_avito_stream(phone, username, source_description):
    """
    Создание сделки из потока Авито
    
    Returns:
        int: ID созданной сделки в Битриксе
    """
    normalized_phone = _normalize_phone_for_bitrix(phone)
    contact_id = find_or_create_contact(phone, username)
    
    if not contact_id:
        raise Exception("Не удалось создать/найти контакт")
    
    params = {
        'fields': {
            'TITLE': '+7{} - Авито сообщения'.format(normalized_phone),
            'TYPE_ID': 'SALE',
            'STAGE_ID': 'NEW',
            'SOURCE_ID': 'AvitoMessanger',
            'SOURCE_DESCRIPTION': source_description,
            'CATEGORY_ID': '28',
            'CONTACT_ID': contact_id,
            'ASSIGNED_BY_ID': '1052',
        }
    }

    # crm.deal.add возвращает ID сделки напрямую
    deal_id = bitrix.call('crm.deal.add', params)
    return int(deal_id) if deal_id else None


def find_or_create_contact(phone, username):
    """
    Ищет существующий контакт по телефону, или создает новый если не найден.
    Оптимизация: избегает дублирования контактов и снижает нагрузку на API.
    
    Returns:
        int: ID контакта в Битриксе
    """
    normalized_phone = _normalize_phone_for_bitrix(phone)
    phone_with_code = f"7{normalized_phone}"
    
    # 1. Поиск существующего контакта по телефону
    search_params = {
        'filter': {'PHONE': phone_with_code},
        'select': ['ID'],  # Только ID, не все поля!
        'start': -1  # Отключить подсчет общего количества
    }
    
    try:
        result = bitrix.call('crm.contact.list', search_params)
        # fast_bitrix24 возвращает список контактов напрямую
        if result and len(result) > 0:
            contact_id = result[0].get('ID') or result[0].get('id')
            if contact_id:
                return int(contact_id)
    except Exception as e:
        # Если поиск не удался, продолжаем создание
        import logging
        logging.warning(f"Ошибка поиска контакта: {e}, создаем новый")
    
    # 2. Контакт не найден - создаем новый
    create_params = {
        'fields': {
            'NAME': username,
            'SOURCE_ID': 'Avito',
            'SOURCE_DESCRIPTION': 'Avito - Сообщение от {}'.format(username),
            'HAS_PHONE': 'Y',
            'PHONE': [{
                'VALUE': phone_with_code,
                'VALUE_TYPE': 'WORK',
                "TYPE_ID": "PHONE"
            }]
        }
    }

    # crm.contact.add возвращает ID контакта напрямую
    contact_id = bitrix.call('crm.contact.add', create_params)
    return int(contact_id) if contact_id else None


def create_contact(phone, username):
    """Deprecated: используйте find_or_create_contact"""
    return find_or_create_contact(phone, username)


def create_source(source_name, source_id):
    params = {
        'fields': {
            'ENTITY_ID': 'SOURCE',
            'STATUS_ID': source_id,
            'NAME': source_name,
            'SORT': '110',
            'SYSTEM': 'N',
            'CATEGORY_ID': '0',
        }
    }

    data = bitrix.call('crm.status.add', params)
    print(data)
    return data


def update_source(deal_id, source_id, source_description):
    params = {
        'id': deal_id,
        'fields': {
            'SOURCE_ID': source_id,
            'SOURCE_DESCRIPTION': source_description,
        }
    }

    data = bitrix.call('crm.deal.update', params)
    return data