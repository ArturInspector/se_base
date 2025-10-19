from threading import Timer
import requests
import config
import json
import bot
import datetime
import logging

logger = logging.getLogger(__name__)


def get_headers(content_type=None):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    params = {
        'grant_type': 'client_credentials',
        'client_id': config.Production.NEW_AVITO_CLIENT_ID,
        'client_secret': config.Production.NEW_AVITO_SECRET
    }
    url = 'https://api.avito.ru/token'
    response = requests.post(url, params=params, headers=headers, timeout=600)

    data = response.json()
    logger.debug(f"Avito token response: {data.get('access_token', 'N/A')[:20]}...")
    token = data['access_token']

    headers = {
        'Authorization': 'Bearer {}'.format(token),
        'accept': 'application/json',
    }
    if content_type is not None:
        headers['Content-Type'] = content_type
    return headers


def get_ad_by_id(ad_id):
    method = '/core/v1/accounts/{}/items/{}/'.format(config.Production.NEW_AVITO_ID, ad_id)

    result = requests.get(config.Production.NEW_AVITO_BASE_URL + method, headers=get_headers())
    return result.json()


def get_stats(items_ids, date_from: datetime.datetime, date_to: datetime.datetime):
    method = '/stats/v1/accounts/{}/items'.format(config.Production.NEW_AVITO_ID)

    data = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d'),
        'fields': ['uniqViews', 'uniqContacts', 'uniqFavorites'],
        'itemIds': items_ids,
        'periodGrouping': 'day'
    }

    result = requests.post(config.Production.NEW_AVITO_BASE_URL + method, headers=get_headers('application/json'), data=json.dumps(data))
    return result.json()


def get_ads(category_id=None, status=None):
    page = 1
    ads = []
    while True:
        res = get_ads_by_page(page, category_id, status)
        if len(res) == 0:
            break
        ads.extend(res)
        page += 1

    return ads


def get_ads_by_page(page, category=None, status=None):
    method = '/core/v1/items'

    params = {
        'per_page': 100,
        'page': page,
    }
    if category is not None:
        params['category'] = category
    if status is not None:
        params['status'] = status

    result = requests.get(config.Production.NEW_AVITO_BASE_URL + method, headers=get_headers(), params=params)
    return result.json()['resources']


def set_webhook(auto_repeat=True):
    try:
        method = '/messenger/v3/webhook'
        params = {
            'url': config.Production.NEW_AVITO_CALLBACK_URL
        }
        
        logger.info(f"Регистрация Avito webhook: {params['url']}")
        
        result = requests.post(
            config.Production.NEW_AVITO_BASE_URL + method, 
            headers=get_headers(content_type='application/json'), 
            data=json.dumps(params),
            timeout=10
        )
        
        if result.status_code == 200:
            logger.info(f"Avito webhook успешно зарегистрирован: {params['url']}")
        else:
            logger.error(f"Ошибка регистрации Avito webhook: {result.status_code} - {result.text}")
            bot.send_message(f'Не удалось подключить вебхук Авито\nURL: {params["url"]}\nStatus: {result.status_code}')
    except Exception as e:
        logger.error(f"Исключение при регистрации Avito webhook: {e}")
    finally:
        Timer(60, set_webhook).start()


def check_context(chat_id):
    try:
        method = '/messenger/v1/accounts/{}/chats/{}'.format(config.Production.NEW_AVITO_ID, chat_id)
        result = requests.get(config.Production.NEW_AVITO_BASE_URL + method, headers=get_headers())

        data = result.json()
        context = data['context']['value']['title']

        if 'Грузчик на подработку' in context:
            return True
        else:
            return False
    except Exception as e:
        bot.send_message('Ошибка проверка контекста чата\n\n{}'.format(str(e)))
        return False


def get_chat(chat_id):
    try:
        method = '/messenger/v2/accounts/{}/chats/{}'.format(config.Production.NEW_AVITO_ID, chat_id)
        result = requests.get(config.Production.NEW_AVITO_BASE_URL + method, headers=get_headers())

        data = result.json()
        logger.debug(f"Get chat {chat_id}: {data['context']['type']} - {data['context']['value']['id']} (status: {result.status_code})")

        return data
    except Exception as e:
        bot.send_message('Ошибка получения чата\n\n{}'.format(str(e)))
        return False


def send_message(chat_id, message, repeat=False, auto_repeat=True, headers=None, error_count=0):
    method = '/messenger/v1/accounts/{}/chats/{}/messages'.format(config.Production.NEW_AVITO_ID, chat_id)

    params = {
        "message": {
            "text": message
        },
        "type": "text"
    }
    if headers is None:
        headers = get_headers()
    result = requests.post(config.Production.NEW_AVITO_BASE_URL + method, headers=headers, data=json.dumps(params), timeout=15)

    if result.status_code != 200:
        bot.send_message('[Avito] Не удалось отправить сообщение на Авито\n\nchat_id: {}\nmessage: {}\nСтатус код: {}\n\nПовторная отправка через 5 секунд'.format(
            chat_id, message, result.status_code
        ))
        if auto_repeat and error_count < 10:
            Timer(5, send_message, args=(chat_id, message, True, auto_repeat, headers, error_count + 1 )).start()
        return False
    else:
        logger.debug(f"Message sent to {chat_id}: {message[:50]}...")
        if repeat:
            bot.send_message('Ранее недоставленное сообщение в чат {} - доставлено'.format(chat_id))

    return True


def get_calls_by_date(date: datetime.datetime):
    # method = '/calltracking/v1/getCalls/'
    method = '/calltracking/v1/getCalls/'

    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    finish = date.replace(hour=23, minute=59, second=59, microsecond=0)

    data = {
        'dateTimeFrom': start.isoformat() + '+03:00',
        'dateTimeTo': finish.isoformat() + '+03:00',
        'limit': 100,
        'offset': 0
    }

    logger.debug(f"Getting Avito calls: {data}")

    headers = get_headers()
    headers['Content-Type'] = 'application/json'

    result = requests.post(config.Production.NEW_AVITO_BASE_URL + method, headers=headers, data=json.dumps(data), timeout=15)
    if result.status_code != 200:
        return []
    else:
        return result.json()['calls']


def get_category_by_ad_id(ad_id):
    ads_list = get_ads()

    for ad in ads_list:
        if ad['id'] == ad_id:
            return ad['category']
    return None
