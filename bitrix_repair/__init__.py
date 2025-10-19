import recalls.bitrix
import avito_old
import avito_new
import bitrix
import datetime
import utils


def repair_avito_status(date: datetime.datetime):
    avito_calls = avito_old.api.get_calls_by_date(date)
    bitrix_deals = bitrix.api.get_deals_by_date(date)

    phones = []

    cnt = 0
    for call in avito_calls:
        cnt += 1
        phone = utils.telephone(call['buyerPhone'])
        if phone in phones:
            continue
        phones.append(phone)
        for deal in bitrix_deals:
            deal_phone = utils.telephone(deal['TITLE'])
            if deal_phone != phone:
                continue
            if deal_phone is None:
                continue
            if deal['SOURCE_ID'] == 'AvitoCall':
                continue

            recalls.bitrix.update_source(deal['ID'], 'AvitoCall', 'Авито')


def repair_avito_status_new(date: datetime.datetime):
    avito_calls = avito_new.api.get_calls_by_date(date)
    bitrix_deals = bitrix.api.get_deals_by_date(date)

    phones = []

    cnt = 0
    for call in avito_calls:
        cnt += 1
        phone = utils.telephone(call['buyerPhone'])
        if phone in phones:
            continue
        phones.append(phone)
        for deal in bitrix_deals:
            deal_phone = utils.telephone(deal['TITLE'])
            if deal_phone != phone:
                continue
            if deal_phone is None:
                continue
            if deal['SOURCE_ID'] == 'AvitoCall':
                continue

            recalls.bitrix.update_source(deal['ID'], 'AvitoCall', 'Авито')