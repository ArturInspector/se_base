import datetime
import traceback

import bitrix
import bot
import utils
import notifications
import cache

DEAL_KEYS = []
GRUZ_IDS = [9, 113, 190, 196, 198, 200, 202, 620, 624, 204, 628, 632, 552, 636, 586, 640, 1350, 1352, 644, 648, 1354,
            1356, 652, 1358, 656, 658, 1360, 1362, 660, 662, 1364, 1366, 664, 1368, 1370, 668, 670, 1372, 1374, 674]

BAD_IDS = {
    9: 'Некачественный лид',
    1758: 'Некачественный лид',
    2046: 'Трудоустройство',
    2060: 'не нашли технику (физ)',
    2066: 'дорого техника (физ)',
    113: 'Некачественный лид',
    176: 'Отказ',
    2080: 'Повторный клиент',
    2082: 'Ошибочный звонок',
    2090: 'Спам (реклама)',
    578: 'спам (реклама)',
    1546: 'Повторный клиент',
    192: 'Спам (реклама)',
    580: 'трудоустройство',
    1624: 'Некачественный лид',
    194: 'Трудоустройство',
    582: 'непрофильный запрос',
    752: 'Некачественный лид',
    1024: 'Некачественный лид',
    1656: 'Спам (реклама)',
    1028: 'Непрофильный запрос',
    1518: 'Спам (реклама)',
    1658: 'Трудоустройство',
    1520: 'Трудоустройство',
    586: 'не нашли технику (физ)',
    636: 'не нашли технику (физ)',
    638: 'не нашли технику (юр)',
    1354: 'дорого техника (физ)',
    1672: 'не нашли технику (физ)',
    1558: 'Повторный клиент',
    1562: 'Ошибочный звонок',
    1678: 'дорого техника (физ)',
    648: 'дорого техника (физ)',
    650: 'дорого техника (юр)',
    1370: 'Повторный клиент',
    1372: 'Ошибочный звонок',
    1702: 'Повторный клиент',
    1580: 'дорого техника (физ)',
    1704: 'Ошибочный звонок',
    666: 'перезвон - не звонил кл',
    1582: 'не нашли технику (физ)',
    668: 'повторный клиент',
    1056: 'Повторный клиент',
    670: 'ошибочный звонок',
    1058: 'Ошибочный звонок',
    798: 'Спецтехника без грузчиков ( физ )',
    800: 'Спецтехника без грузчиков (юр )',
    688: 'Некачественный лид',
    886: 'Трудоустройство',
    982: 'не нашли технику (физ)',
    994: 'дорого техника (физ)',
    1012: 'Повторный клиент',
    1020: 'Ошибочный звонок',
    884: 'Спам (реклама)',
    1376: 'Спецтехника без грузчиков (физ)',
    1016: 'Спецтехника без грузчиков (физ)',
    2086: 'Спецтехника без грузчиков (физ)',
    1710: 'Спецтехника без грузчиков (физ)',
    2198: 'Спам'
}

CATEGORIES_IDS = {
    '2': 'Юридические лица',
    '4': 'Колл-центр',
    '10': 'ОП Физические лица',
    '8': 'ОП Юридические лица',
    '46': 'ОП Юридические лица',
    '12': 'Спецтехника',
    '0': 'Грузовой поток',
    '24': 'Грузовой поток - ЮЛ',
    '38': 'Холодные звонки - операторы',
}

DEAL_SUCCESS = [
    'дорого',
    'нет исполнителей',
    'нужно быстрее',
    'нашел у конкурентов',
    'не актуально',
    'не прошли согласование по юристам',
    'не можем выполнить заказ',
    'другая причина',
    'разовый запрос',
]

NEW_BADS = ['отказ', 'повторный клиент', 'спам', 'непрофильный запрос', 'тендер', 'спецтехника']


def processing(data):
    deal_id = data['data[FIELDS][ID]']
    ts = data['ts']
    deal_key = '{}_{}'.format(deal_id, ts)

    check = cache.get_cache('bitrix', key=deal_key)
    if check is not None:
        return

    cache.set_cache('bitrix', key=deal_key, value='1', ex=datetime.timedelta(minutes=10))

    deal = bitrix.api.get_deal_by_id(deal_id)

    if deal is not None:
        n_key = '{}_{}'.format(deal.id, deal.status)
        if n_key in DEAL_KEYS:
            return
        DEAL_KEYS.append(n_key)

    is_gruz = False
    is_no_gruz = False

    print('deal.status_type', deal.status_type)
    if deal.status_type == -1:
        print('status_obj', deal.status_obj)
        if int(deal.status_obj['ID']) in BAD_IDS:
            print('bad status')
            return
        print("deal.status_obj['ID']", deal.status_obj['ID'])
        phone = utils.telephone(deal.title)
        is_moscow = False
        if phone is not None:
            phone_region = utils.get_phone_region(phone)
            is_moscow = utils.is_moscow_str(phone_region)

        category = CATEGORIES_IDS.get(deal.status_obj['CATEGORY_ID'])
        print('category', category)
        if category is None:
            return

        try:
            text = "Воронка: {}\n\n{}".format(category if category is not None else 'Не определена', deal.get_description())
        except:
            print(traceback.format_exc())
            return

        if deal.status_obj['CATEGORY_ID'] == '46':
            #notifications.send_me('#TESTQ DEAL {} IN'.format(deal.id))
            ch = False
            for s in DEAL_SUCCESS:
                if s.lower() in str(deal.status).lower():
                    ch = True
                    break

            for s in NEW_BADS:
                try:
                    if s in deal.status_obj['NAME'].lower():
                        print('____ baddd!!!')
                        return
                except:
                    print(traceback.format_exc())
            print('GRUZ BOT')
            print(text)
            notifications.gruz_message(text)
        else:
            print('PRIMARY BOT')
            print(text)
            notifications.send_message(text)

        return
        if int(deal.status_obj['ID']) not in [578, 738, 884, 722, 1002, 658, 580, 886]:
            is_no_gruz = True
        if int(deal.status_obj['ID']) in GRUZ_IDS:
            is_gruz = True

        print(int(deal.status_obj['ID']), is_gruz, is_no_gruz)
        if is_gruz is False and is_no_gruz is False:
            return

        if is_gruz:
            notifications.gruz_message(deal.get_description())
        if is_no_gruz:
            notifications.send_message(deal.get_description())

        phone = utils.telephone(deal.title)
        if phone is None:
            return
        if len(phone) == 0:
            return
        calls_list = bitrix.calls.find_calls(phone, deal.create_date, deal.get_max_date())

        if len(calls_list) == 0:
            return

        for call in calls_list:
            message = 'Звонок по сделке #{}\nот {}'.format(deal.id,
                                                           call.date.strftime('%d.%m.%Y %H:%M'))
            if is_gruz:
                notifications.gruz_message(message, call.link)
            if is_no_gruz:
                notifications.send_message(message, call.link)


def get_report():
    deals = bitrix.api.get_today()
    now = datetime.datetime.now()

    cnt = 0
    message = 'Отчет за {}'.format(now.strftime('%d.%m.%Y %H:%M'))
    message += '\n\nЗаявки с городских номеров'
    for d in deals:
        if d.status_type == -1:
            continue
        phone = utils.telephone(d.title)
        if phone is None:
            continue
        if phone[0] == '9':
            continue
        if d.status_type == 0:
            continue
        #print('{}: {} - #{}'.format(utils.format_phone(phone), d.status_type, d.id))
        message += '\n{}'.format(
            utils.format_phone(phone), d.id
        )
        cnt += 1

    message += '\n\nСделки ТАКЕЛАЖ:'
    for d in deals:
        if d.status_type == -1:
            continue
        if 'ТАКЕЛАЖ' not in d.services:
            continue
        phone = d.get_phone()
        if len(phone) == 0:
            phone = 'https://standartexpress.bitrix24.ru/crm/deal/details/{}/'.format(d.id)
        message += '\n{}'.format(
            phone
        )

    print(message)
    notifications.send_message(message)
