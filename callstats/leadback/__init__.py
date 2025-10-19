import datetime
import requests


def get_calls(date: datetime.datetime, page=0):
    url = 'https://leadback.ru/api/calls.php'
    params = {
        'secret_key': '23d28d0246a000142e893d1c5c0bf949',
        'client_id': '44696b2e014d890608035c2ab04e71be',
        'date': date.strftime('%Y-%m-%d'),
        'limit': 100,
        'offset': 100 * page
    }

    response = requests.get(url, params=params)

    result = response.json()['data']

    if len(result) > 0:
        result.extend(get_calls(date, page + 1))

    return result
