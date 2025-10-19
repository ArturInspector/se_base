from typing import List
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import utils

credentials_file = '{}/token.json'.format(utils.get_script_dir())


def get_phones() -> List[str]:
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(credentials)

    wks = client.open_by_url(
        'https://docs.google.com/spreadsheets/d/1foBLXa3pSzNpkyivMNp486vzJno0qMCO7LZUItL984U/edit#gid=795301951')

    sheets = wks.worksheets()
    worksheet = sheets[1]

    data = worksheet.get_all_values()
    phones = []

    for d in data:
        phone = utils.telephone(d[3])
        if phone is not None:
            phones.append(phone)
    return phones
