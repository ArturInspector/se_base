from .entities import BitrixDeal
from typing import List, Dict
import datetime
import config
import json
import requests


def get_today():
    statuses = get_statuses_full()
    deals = get_deals_today()

    result = [BitrixDeal(deal, statuses[deal['STAGE_ID']]) for deal in deals]
    return result


def get_deals_today(start=0):
    now = datetime.datetime.now()
    d = now.strftime('%Y-%m-%d') + ' 00:00:00'
    response = requests.get(
        url=config.Production.bitrix_webhook + 'crm.deal.list.json?FILTER[>DATE_CREATE]={}'
                                               '&SELECT[]=*'
                                               '&SELECT[]=UF_*'
                                               '&start={}'.format(d, start),
    )

    data = response.json()
    orders = [order for order in data['result']]

    if data.get('next') is not None:
        orders.extend(get_deals_today(data['next']))
    return orders


def get_test_deals():
    now = datetime.datetime.now() - datetime.timedelta(days=1)
    now = now.replace(hour=15, minute=30)
    d = now.strftime('%Y-%m-%d %H:%M:%S')
    response = requests.get(
        url=config.Production.bitrix_webhook + 'crm.deal.list.json?FILTER[>DATE_CREATE]={}'
                                               '&FILTER[CATEGORY_ID]=46'
                                               '&SELECT[]=*&start=50'.format(d),
    )

    print(response.request.url)
    data = response.json()
    statuses = get_statuses_full()
    deals = [BitrixDeal(deal, statuses[deal['STAGE_ID']]) for deal in data['result']]
    return deals


def get_deals_by_date(date: datetime.datetime, start=0):
    start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
    finish_date = date.replace(hour=23, minute=59, second=59, microsecond=0)

    start_date = start_date.strftime('%Y-%m-%d') + ' 00:00:00'
    finish_date = finish_date.strftime('%Y-%m-%d') + ' 23:59:59'

    url = config.Production.bitrix_webhook + 'crm.deal.list.json?FILTER[>DATE_CREATE]={}&FILTER[<DATE_CREATE]={}&SELECT[]=*&SELECT[]=UF_*&start={}'.format(start_date, finish_date, start)

    response = requests.get(
        url=url,
    )

    data = response.json()
    orders = [order for order in data['result']]

    next_value = data.get('next')

    if next_value is not None:
        orders.extend(get_deals_by_date(date, data['next']))
    return orders


def get_leads_by_date(date: datetime.datetime, start=0):
    start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
    finish_date = date.replace(hour=23, minute=59, second=59, microsecond=0)

    start_date = start_date.strftime('%Y-%m-%d') + ' 00:00:00'
    finish_date = finish_date.strftime('%Y-%m-%d') + ' 23:59:59'

    url = config.Production.bitrix_webhook + 'crm.lead.list.json?FILTER[>DATE_CREATE]={}&FILTER[<DATE_CREATE]={}&SELECT[]=*&SELECT[]=UF_*&start={}'.format(start_date, finish_date, start)

    response = requests.get(
        url=url,
    )

    data = response.json()
    orders = [order for order in data['result']]

    next_value = data.get('next')

    if next_value is not None:
        orders.extend(get_leads_by_date(date, data['next']))
    return orders


def get_deal_by_id(deal_id):
    response = requests.get(
        config.Production.bitrix_webhook + 'crm.deal.get.json',
        params={'ID': deal_id}
    )
    deal = response.json()['result']
    print(json.dumps(deal, ensure_ascii=False, indent=3))
    statuses = get_statuses_full()
    print(statuses[deal['STAGE_ID']])
    return BitrixDeal(deal, statuses[deal['STAGE_ID']])


def get_contact_by_id(contact_id):
    response = requests.get(
        config.Production.bitrix_webhook + 'crm.contact.get.json',
        params={'ID': contact_id}
    )
    contact = response.json()['result']
    # print(json.dumps(deal, ensure_ascii=False, indent=3))
    return contact


def get_lead_by_id(lead_id):
    response = requests.get(
        config.Production.bitrix_webhook + 'crm.lead.get.json',
        params={'ID': lead_id}
    )
    lead = response.json()['result']
    # print(json.dumps(deal, ensure_ascii=False, indent=3))
    return lead


def get_statuses_full():
    response = requests.get(
        config.Production.bitrix_webhook + 'crm.status.list.json'
    )

    statuses = response.json()['result']

    result = {}

    for status in statuses:
        result[status['STATUS_ID']] = status

    return result


def get_statuses():
    response = requests.get(
        config.Production.bitrix_webhook + 'crm.status.list.json'
    )

    statuses = response.json()['result']

    return statuses


def find_statuses(statuses_str: List[str]) -> Dict[int, str]:
    statuses_str = [s.lower() for s in statuses_str]

    statuses = get_statuses()

    result = {}

    for status in statuses:
        name = status['NAME'].lower()
        if name in statuses_str:
            result[int(status['ID'])] = status['NAME']
    return result


def test():
    response = requests.get(
        config.Production.bitrix_webhook + 'crm.status.list.json'
    )

    result = response.json()['result']
    print(json.dumps(result, ensure_ascii=False, indent=3))