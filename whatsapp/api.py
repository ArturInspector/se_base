import requests
import config


def send_message(phone, text: str, is_business=False):
    headers = {
        'Authorization': 'Bearer {}'.format(config.Production.WHAPI_TOKEN if is_business is False else config.Production.WHAPI_BUSINESS_TOKEN),
        'Content-Type': 'application/json'
    }
    method = '/messages/text'
    url = '{}/{}'.format(config.Production.WHAPI_BASE_URL, method)

    if phone is not None:
        phone = '7{}@s.whatsapp.net'.format(phone)

    data = {
        'body': text,
        'to': phone
    }

    result = requests.post(url, json=data, headers=headers)
    print(result.status_code)
    print(result.text)