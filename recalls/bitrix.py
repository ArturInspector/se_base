from fast_bitrix24 import Bitrix
import config
import utils

bitrix = Bitrix(config.Production.BITRIX_WEBHOOK)
chat_bitrix = Bitrix(config.Production.chatbot_bitrix_webhook)


def _normalize_phone_for_bitrix(phone: str) -> str:
    """
    Централизованная нормализация телефона для Битрикса
    Принцип: DRY - одна функция для всех случаев
    
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

    data = bitrix.get_all('crm.deal.update', params=params)
    return data


def create_deal_from_avito(phone, username, source_description):
    normalized_phone = _normalize_phone_for_bitrix(phone)
    contact_id = create_contact(phone, username)
    
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

    data = bitrix.get_all('crm.deal.add', params=params)
    return data


def create_deal_from_avito_stream(phone, username, source_description):
    normalized_phone = _normalize_phone_for_bitrix(phone)
    contact_id = create_contact(phone, username)
    
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

    data = bitrix.get_all('crm.deal.add', params=params)
    return data


def create_contact(phone, username):
    normalized_phone = _normalize_phone_for_bitrix(phone)
    phone_with_code = f"7{normalized_phone}"
    
    params = {
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

    data = bitrix.get_all('crm.contact.add', params=params)
    return data


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

    data = bitrix.get_all('crm.status.add', params=params)
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

    data = bitrix.get_all('crm.deal.update', params=params)
    return data