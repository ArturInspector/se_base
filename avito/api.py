from threading import Timer
import requests
import config
import json
import bot
import datetime
import avito_old


def get_headers(content_type=None):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    params = {
        'grant_type': 'client_credentials',
        'client_id': config.Production.AVITO_CLIENT_ID,
        'client_secret': config.Production.AVITO_SECRET
    }
    url = 'https://api.avito.ru/token'
    response = requests.post(url, params=params, headers=headers, timeout=600)

    data = response.json()
    token = data['access_token']

    headers = {
        'Authorization': 'Bearer {}'.format(token),
        'accept': 'application/json',
    }
    if content_type is not None:
        headers['Content-Type'] = content_type
    return headers


def get_ad_by_id(ad_id):
    method = '/core/v1/accounts/{}/items/{}/'.format(config.Production.AVITO_ID, ad_id)

    result = requests.get(config.Production.AVITO_BASE_URL + method, headers=get_headers())
    return result.json()


def get_item_details(item_id):
    """
    Получает детали объявления через новый API endpoint
    https://api.avito.ru/items/v1/items/{item_id}
    """
    try:
        url = f'https://api.avito.ru/items/v1/items/{item_id}'
        headers = get_headers()
        
        result = requests.get(url, headers=headers, timeout=10)
        result.raise_for_status()
        
        data = result.json()
        print(f"DEBUG: API ответ для item_id {item_id}: {data}")
        return data
        
    except Exception as e:
        print(f"DEBUG: Ошибка при получении данных объявления {item_id}: {e}")
        return None


def get_stats(items_ids, date_from: datetime.datetime, date_to: datetime.datetime):
    method = '/stats/v1/accounts/{}/items'.format(config.Production.AVITO_ID)

    data = {
        'dateFrom': date_from.strftime('%Y-%m-%d'),
        'dateTo': date_to.strftime('%Y-%m-%d'),
        'fields': ['uniqViews', 'uniqContacts', 'uniqFavorites'],
        'itemIds': items_ids,
        'periodGrouping': 'day'
    }

    result = requests.post(config.Production.AVITO_BASE_URL + method, headers=get_headers('application/json'), data=json.dumps(data))
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

    result = requests.get(config.Production.AVITO_BASE_URL + method, headers=get_headers(), params=params)
    return result.json()['resources']


def set_webhook():
    try:
        method = '/messenger/v3/webhook'

        params = {
            'url': config.Production.AVITO_CALLBACK_URL
        }

        print(params)

        result = requests.post(config.Production.AVITO_BASE_URL + method, headers=get_headers(), data=json.dumps(params))
        print(result.text)
        print(result.status_code)
        print(result.json())
        if result.status_code != 200:
            bot.send_message('Не удалось подключить вебхук Авито')
    finally:
        Timer(60, set_webhook).start()


def check_context(chat_id):
    try:
        method = '/messenger/v1/accounts/{}/chats/{}'.format(config.Production.AVITO_ID, chat_id)
        result = requests.get(config.Production.AVITO_BASE_URL + method, headers=get_headers())

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
        method = '/messenger/v2/accounts/{}/chats/{}'.format(config.Production.AVITO_ID, chat_id)
        result = requests.get(config.Production.AVITO_BASE_URL + method, headers=get_headers())

        data = result.json()
        print(data['context']['type'], data['context']['value']['id'])
        print(result.status_code)

        return data
    except Exception as e:
        bot.send_message('Ошибка получения чата\n\n{}'.format(str(e)))
        return False


def send_message(chat_id, message, repeat=False, auto_repeat=True, headers=None, error_count=0):
    method = '/messenger/v1/accounts/{}/chats/{}/messages'.format(config.Production.AVITO_ID, chat_id)

    params = {
        "message": {
            "text": message
        },
        "type": "text"
    }
    if headers is None:
        headers = get_headers()
    result = requests.post(config.Production.AVITO_BASE_URL + method, headers=headers, data=json.dumps(params), timeout=15)

    if result.status_code != 200:
        print(f'[Avito] Не удалось отправить сообщение на Авито\n\nchat_id: {chat_id}\nmessage: {message}\nСтатус код: {result.status_code}\n\nПовторная отправка через 5 секунд')
        print(f'Ответ сервера: {result.text}')
        if auto_repeat and error_count < 10:
            Timer(5, send_message, args=(chat_id, message, True, auto_repeat, headers, error_count + 1 )).start()
        return False
    else:
        print('aga')
        if repeat:
            print(f'Ранее недоставленное сообщение в чат {chat_id} - доставлено')

    return True


def get_calls_by_date(date: datetime.datetime):
    # method = '/calltracking/v1/getCalls/'
    method = '/cpa/v2/callsByTime'

    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    finish = date.replace(hour=23, minute=59, second=59, microsecond=0)

    data = {
        'dateTimeFrom': start.isoformat() + '+03:00',
        'dateTimeTo': finish.isoformat() + '+03:00',
        'limit': 100,
        'offset': 0
    }

    print(data)

    headers = get_headers()
    headers['Content-Type'] = 'application/json'

    result = requests.post(config.Production.AVITO_BASE_URL + method, headers=headers, data=json.dumps(data), timeout=15)
    print(result.json())


def get_category_by_ad_id(ad_id):
    ads_list = get_ads()

    for ad in ads_list:
        if ad['id'] == ad_id:
            return ad['category']
    return None