from typing import Union
import datetime
import requests
import config


def get_calls(date: datetime.datetime, user_id=None, page=0):
    yesterday = date - datetime.timedelta(days=1)
    start_date = yesterday.replace(hour=21, minute=0, second=0, microsecond=0)
    finish_date = date.replace(hour=21, minute=0, second=0, microsecond=0)

    headers = {
        'X-MPBX-API-AUTH-TOKEN': config.Production.BEELINE_TOKEN
    }

    date_from = start_date.isoformat() + 'Z'
    date_to = finish_date.isoformat() + 'Z'

    params = {
        'dateFrom': date_from,
        'dateTo': date_to,
        'userId': user_id,
        'page': page,
        'pageSize': 100
    }

    response = requests.get('https://cloudpbx.beeline.ru/apis/portal/v2/statistics', params=params, headers=headers)

    calls_list = response.json()

    if len(calls_list) > 0:
        calls_list.extend(get_calls(date, user_id, page + 1))
    return calls_list
