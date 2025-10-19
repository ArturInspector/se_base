from .entities import Call
import requests
import config
import datetime
import bot

HEADERS = {'X-MPBX-API-AUTH-TOKEN': '71828703-a7e4-4f0d-8d35-aaf81169f577', 'Content-Type': 'application/json'}


def find_calls(phone, date_start: datetime.datetime, date_end: datetime.datetime):
    print('find {} {} {}'.format(phone, date_start, date_end))
    calls_list = get_calls(date_start, date_end)
    links = []

    for call in calls_list:
        if phone in call['phone']:
            try:
                link = get_record_link(call)
                date = datetime.datetime.fromtimestamp(call['date'] / 1000)
                links.append(Call(date, link))
            except Exception as e:
                print(e)
                continue
    return links


def get_record_link(call):
    response = requests.get(
        config.Production.BEELINE_URL + 'v2/records/{}/{}/download'.format(call['externalId'], call['abonent']['userId']),
        headers=HEADERS
    )
    return response.content


def get_calls(date_start: datetime.datetime, date_end: datetime.datetime, last_id=None):
    date_from = date_start - datetime.timedelta(hours=3, minutes=10)
    date_to = date_end + datetime.timedelta(hours=3, minutes=10)
    params = {
        'dateFrom': date_from.isoformat()[:-6] + '+00:00',
        'dateTo': date_to.isoformat()[:-6] + '+00:00',
    }
    if last_id is not None:
        params['id'] = last_id
    response = requests.get(
        config.Production.BEELINE_URL + 'records',
        headers=HEADERS,
        params=params
    )

    calls = response.json()
    if isinstance(calls, list) is False:
        return []
    if len(calls) != 0:
        calls.extend(get_calls(date_start, date_end, calls[-1]['id']))
    return calls