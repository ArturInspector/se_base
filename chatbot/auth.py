import config
import requests


def get_auth_url():
    url = '{}/oauth/authorize/?client_id={}'.format(config.Production.BITRIX_APP_URL,
                                                    config.Production.BITRIX_APP_CLIENT_ID)
    return url


def get_access_token(code):
    url = 'https://oauth.bitrix.info/oauth/token/'

    params = {
        'grant_type': 'authorization_code',
        'client_id': config.Production.BITRIX_APP_CLIENT_ID,
        'client_secret': config.Production.BITRIX_APP_CLIENT_SECRET,
        'code': code
    }

    response = requests.get(url, params=params)
    access_token = response.json()['access_token']

    return access_token