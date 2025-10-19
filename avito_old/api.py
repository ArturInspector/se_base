from threading import Timer
from typing import Union
import traceback
import requests
import config
import json
import bot
import datetime
import utils
import time
import report_bot


COOKIES = 'srv_id=FdDfrGJYIDpcJPue.d4_wdD3Umv7L5HGgrE2TkkxNlie9LZ1K56TQKd03vJFbYuGjl1xGjsuEbKL4gVrgTiHy.9ojosZIDIu9cYXIvigzAK7S9HAHESLCm5sJnhBVb7ng=.web; gMltIuegZN2COuSe=EOFGWsm50bhh17prLqaIgdir1V0kgrvN; u=32mfcknr.1fd84dv.15axrzomnan00; v=1722591439; dfp_group=48; _gcl_au=1.1.2025012667.1722591440; _ga=GA1.1.928642997.1722591440; __ai_fp_uuid=c9a7cdd33b66ac7b%3A1; _ym_uid=1722591440588806448; _ym_d=1722591440; __upin=lV0GwANPKXnJviOmKSKSvg; tmr_lvid=5e9cedbe070999a28279f317bb4b2bb7; tmr_lvidTS=1722591440512; _ym_isad=1; yandex_monthly_cookie=true; _ym_visorc=b; domain_sid=lZ7WkWJEKoQHMtwBUOjzH%3A1722591441438; uxs_uid=d12e2dc0-50b2-11ef-b800-796d79b1d6bf; adrdel=1722591441677; adrdel=1722591441677; adrcid=Aa9AlIjgl5J0Jy4ORXFu2lg; adrcid=Aa9AlIjgl5J0Jy4ORXFu2lg; __zzatw-avito=MDA0dBA=Fz2+aQ==; __zzatw-avito=MDA0dBA=Fz2+aQ==; _buzz_fpc=JTdCJTIydmFsdWUlMjIlM0ElN0IlMjJ1ZnAlMjIlM0ElMjIzNjZiMDc4MThiNDg3ZGRhYmMxM2FmNGViY2QzYTY4MCUyMiUyQyUyMmJyb3dzZXJWZXJzaW9uJTIyJTNBJTIyMTI3LjAlMjIlMkMlMjJ0c0NyZWF0ZWQlMjIlM0ExNzIyNTkxNDQwMTEyJTdEJTJDJTIycGF0aCUyMiUzQSUyMiUyRiUyMiUyQyUyMmRvbWFpbiUyMiUzQSUyMi53d3cuYXZpdG8ucnUlMjIlMkMlMjJleHBpcmVzJTIyJTNBJTIyU2F0JTJDJTIwMDIlMjBBdWclMjAyMDI1JTIwMDklM0EzNyUzQTIxJTIwR01UJTIyJTJDJTIyU2FtZVNpdGUlMjIlM0ElMjJMYXglMjIlN0Q=; _buzz_aidata=JTdCJTIydmFsdWUlMjIlM0ElN0IlMjJ1ZnAlMjIlM0ElMjJsVjBHd0FOUEtYbkp2aU9tS1NLU3ZnJTIyJTJDJTIyYnJvd3NlclZlcnNpb24lMjIlM0ElMjIxMjcuMCUyMiUyQyUyMnRzQ3JlYXRlZCUyMiUzQTE3MjI1OTE0NDA0OTklN0QlMkMlMjJwYXRoJTIyJTNBJTIyJTJGJTIyJTJDJTIyZG9tYWluJTIyJTNBJTIyLnd3dy5hdml0by5ydSUyMiUyQyUyMmV4cGlyZXMlMjIlM0ElMjJTYXQlMkMlMjAwMiUyMEF1ZyUyMDIwMjUlMjAwOSUzQTM3JTNBMjElMjBHTVQlMjIlMkMlMjJTYW1lU2l0ZSUyMiUzQSUyMkxheCUyMiU3RA==; f=5.0c4f4b6d233fb90636b4dd61b04726f147e1eada7172e06c47e1eada7172e06c47e1eada7172e06c47e1eada7172e06cb59320d6eb6303c1b59320d6eb6303c1b59320d6eb6303c147e1eada7172e06c8a38e2c5b3e08b898a38e2c5b3e08b890df103df0c26013a7b0d53c7afc06d0b2ebf3cb6fd35a0ac0df103df0c26013a8b1472fe2f9ba6b9e2bfa4611aac769efa4d7ea84258c63d59c9621b2c0fa58f915ac1de0d034112f12b79bbb67ac37d46b8ae4e81acb9fae2415097439d40477fde300814b1e85546b8ae4e81acb9fa34d62295fceb188dd99271d186dc1cd03de19da9ed218fe2d50b96489ab264edd50b96489ab264ed3de19da9ed218fe246b8ae4e81acb9fa38e6a683f47425a8352c31daf983fa077a7b6c33f74d335c84df0fd22b85d35fc34238d0bd261b67cb5ec09fa5c57cfad44c4f58a3d78080550369b42c8b7eb717c7721dca45217bc8bec9d424510011ba695b4034544747e2415097439d404746b8ae4e81acb9fa786047a80c779d5146b8ae4e81acb9fa99e842ed979b3794fed88e598638463b2da10fb74cac1eab3fdb0d9d9f6f145bd1ce76042dff8395312f8fecc8ca5e543486a07687daa291; ft="SI6UqWKl+bLBaKHEcZIXixJdfvz+Xme+DyO0IqwFyQ1MsfYce78ZBG3hF0CRFueoPsIkzELkVOx8BLeMWmShZ4Q5n67RzDr9SZ5LlOygNj3+qhZ72KsSi63Uz9ZXY1WJEJUbieH9g8VZdrua5p69bo5btAVTrWldozEsnNeHoxpz8A89W0pAQVL/JeHVhBkW"; cfidsw-avito=XkpO5MFmvNYZ4MgL4sTp06E3q51bUPegDw9G5sJWkuLvvOV4SyBrO/yJpnkVKsX8PMv5FZJ2NyJdiQ6eRTLGhcO3Uq+ZZJtVtqpwtiFSFNSmUGf0jtcjRSkZyjafuCmvhSt8tG6xpcv1jPkLl1qFZGSujwTZRequtBl5; cfidsw-avito=XkpO5MFmvNYZ4MgL4sTp06E3q51bUPegDw9G5sJWkuLvvOV4SyBrO/yJpnkVKsX8PMv5FZJ2NyJdiQ6eRTLGhcO3Uq+ZZJtVtqpwtiFSFNSmUGf0jtcjRSkZyjafuCmvhSt8tG6xpcv1jPkLl1qFZGSujwTZRequtBl5; sessid=611c59dab961ce0dec1c0ea966f2eed0.1722591448; cfidsw-avito=mdPNQ1tzqdOxY/wKcfsktthcDqHMJ+2cOb2uBAf24TPVWrRAlBipejkTcg66n7jhLo3eBbZSwEE++Fb3VkpedvW1MoQfjgCPD/0vatT/AEucAN0ziMGAYgzg/yViKsl3Fmmfo+oDPtfWq02JBX0HbUvMwjrbZcjSoLYT; buyer_laas_location=650400; luri=kazan; buyer_location_id=650400; isLegalPerson=1; cartCounter=0; redirectMav=1; sx=H4sIAAAAAAAC%2FwTAQQ6CMBQE0LvM2oVAmfH3NtBfNcQ0JmA1NL27r4Ekk4t3o80MtKw1T%2BaarynJDbGhImJ%2FcPP1eZzlXN57GcpWp%2B%2FntVRTOH7CBRlx0DhSujH0%2Fg8AAP%2F%2FC0yKslsAAAA%3D; buyer_from_page=main; _ga_WW6Q1STJ8M=GS1.1.1722591466.1.0.1722591466.0.0.0; _ga_ZJDLBTV49B=GS1.1.1722591467.1.0.1722591467.0.0.0; abp=0; _ga_M29JC28873=GS1.1.1722591440.1.1.1722591468.32.0.0; tmr_detect=0%7C1722591473273'


def get_headers(content_type=None):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    params = {
        'grant_type': 'client_credentials',
        'client_id': config.Production.OLD_AVITO_CLIENT_ID,
        'client_secret': config.Production.OLD_AVITO_SECRET
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
    method = '/core/v1/accounts/{}/items/{}/'.format(config.Production.OLD_AVITO_ID, ad_id)

    result = requests.get(config.Production.AVITO_BASE_URL + method, headers=get_headers())
    return result.json()


def get_stats(items_ids, date_from: datetime.datetime, date_to: datetime.datetime):
    method = '/stats/v1/accounts/{}/items'.format(config.Production.OLD_AVITO_ID)

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
            'url': config.Production.OLD_AVITO_CALLBACK_URL
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
        method = '/messenger/v1/accounts/{}/chats/{}'.format(config.Production.OLD_AVITO_ID, chat_id)
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


def send_message(chat_id, message, repeat=False, auto_repeat=True, headers=None, error_count=0):
    method = '/messenger/v1/accounts/{}/chats/{}/messages'.format(config.Production.OLD_AVITO_ID, chat_id)

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
        bot.send_message('[Avito OLD] Не удалось отправить сообщение на Авито\n\nchat_id: {}\nmessage: {}\nСтатус код: {}\n\nПовторная отправка через 5 секунд'.format(
            chat_id, message, result.status_code
        ))
        if auto_repeat and error_count < 10:
            Timer(5, send_message, args=(chat_id, message, True, auto_repeat, headers, error_count + 1)).start()
        return False
    else:
        try:
            print(result.text)
        except:
            pass
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

    print(data)

    headers = get_headers()
    headers['Content-Type'] = 'application/json'

    result = requests.post(config.Production.AVITO_BASE_URL + method, headers=headers, data=json.dumps(data), timeout=15)
    if result.status_code != 200:
        return []
    else:
        return result.json()['calls']


def get_today_messages(page=0):
    method = '/messenger/v2/accounts/{}/chats'.format(config.Production.OLD_AVITO_ID)
    now = datetime.datetime.now()

    headers = get_headers()

    params = {
        'limit': 100,
        'offset': 100 * page,
    }

    result = requests.get(config.Production.AVITO_BASE_URL + method, headers=headers, params=params, timeout=15)
    if result.status_code != 200:
        return []

    all_chats = result.json()['chats']
    chats = []

    is_next = True
    for chat in all_chats:
        updated = datetime.datetime.fromtimestamp(chat['updated'])
        if utils.compare_date(now, updated) is False:
            is_next = False
            break
        else:
            chats.append(chat)

    print(is_next)
    if is_next:
        chats.extend(get_today_messages(page=page + 1))

    return chats




def get_category_by_ad_id(ad_id):
    ads_list = get_ads()

    for ad in ads_list:
        if ad['id'] == ad_id:
            return ad['category']
    return None


def mark_online():
    ads_list = get_ads()
    ads_list = list(filter(lambda ad: ad['status'] == 'active', ads_list))

    bad_answers = {}
    success_count = 0

    cnt = 0
    for ad in ads_list:
        cnt += 1
        result = set_mark_ad(ad['id'])
        if result is None:
            bad_answers[ad['id']] = 'Нет ответа'
        elif result != 200:
            bad_answers[ad['id']] = 'Статус {}'.format(result)
        else:
            success_count += 1

        print(cnt, len(ads_list))
        time.sleep(1)

    message = "#авито gruzchiki-116@mail.ru\n\nАктивных объявлений: {}\nУспешно: {}\n\nОшибки:".format(
        len(ads_list), success_count
    )
    if len(bad_answers) == 0:
        message += ' отсутствуют'
    else:
        for ad_id in bad_answers:
            message += '\n{}: {}'.format(ad_id, bad_answers[ad_id])

    try:
        report_bot.tg_bot.send_message(
            chat_id=125350218,
            text=message
        )
    except:
        print(traceback.format_exc())

    try:
        report_bot.tg_bot.send_message(
            chat_id=344253235,
            text=message
        )
    except:
        print(traceback.format_exc())


def set_mark_ad(ad_id) -> Union[int, None]:
    url = 'https://www.avito.ru/web/1/urgency/items/{}/setUrgency'.format(ad_id)

    data = {
        'value': True
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36',
        'Cookie': COOKIES
    }

    try:
        response = requests.post(url, data=data, headers=headers)
        print(ad_id, response.text)
    except:
        return None
    return response.status_code
