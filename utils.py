from flask import Response, request
from sqlalchemy.ext.declarative import DeclarativeMeta
from string import ascii_lowercase
from typing import Union
import random
import json
import decimal
import datetime
import sys
import os
import inspect
import users
import re
import pymorphy2
import requests


def wrap_links(text: str):
    def repl(m):
        print(m)
        return '<a href="{}">{}</a>'.format(m.group(0), m.group(0))
    url_pattern = 'http[\S]{1,}'

    text = re.sub(url_pattern, repl, text)
    text = text.replace('\n', '<br>')
    return text


def to_json(data):
    data_json = json.dumps(data, ensure_ascii=False, indent=3, default=json_serial)
    return json.loads(data_json)


def format_phone(phone):
    try:
        code = phone[0: 3]
        number = phone[3: 6]
        preffix_1 = phone[6: 8]
        preffix_2 = phone[8: 10]
        return '+7 ({}) {}-{}-{}'.format(code, number, preffix_1, preffix_2)
    except:
        return phone


def telephone(tel):
    # Очищаем номер от всех символов кроме цифр
    clean_tel = re.sub(r'[^\d]', '', str(tel))
    
    # Если номер начинается с 8, заменяем на 7
    if clean_tel.startswith('8') and len(clean_tel) == 11:
        clean_tel = '7' + clean_tel[1:]
    
    # Если номер из 10 цифр, добавляем 7 в начало
    if len(clean_tel) == 10:
        clean_tel = '7' + clean_tel
    
    # Если номер начинается с +7, убираем +
    if clean_tel.startswith('+7'):
        clean_tel = clean_tel[1:]
    
    # Проверяем, что номер корректный (11 цифр, начинается с 7)
    if len(clean_tel) == 11 and clean_tel.startswith('7'):
        return clean_tel[1:]  # Возвращаем без первой 7 для совместимости
    
    # Старый метод как fallback
    pattern = r'(\+7|8|7).*?(\d{3}).*?(\d{3}).*?(\d{2}).*?(\d{2})'
    result = re.findall(pattern, tel)
    phone = ''
    z = 0
    if len(result) == 0:
        return None
    for r in result[0]:
        if z != 0:
            phone += r
        z += 1
    return phone


def get_entity_by_id(entity_id, entities_list):
    result = None
    for entity in entities_list:
        if entity.id == entity_id:
            result = entity
            break
    return result


def get_entity_by_key(key, value, entities_list):
    result = None
    for entity in entities_list:
        if entity.get(key) == value:
            result = entity
            break
    return result


def get_user(session):
    if session.get('user_id') is None:
        return None
    return users.api.get_user_by_id(session.get('user_id'))


class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data)
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            return fields

        return json.JSONEncoder.default(self, obj)


def json_serial(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, datetime.datetime):
        return obj.strftime('%d.%m.%Y %H:%M.%S')
    elif isinstance(obj.__class__, DeclarativeMeta):
        fields = {}
        for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
            if field in ['query', 'registry']:
                continue
            try:
                data = obj.__getattribute__(field)
                json.dumps(data, default=json_serial)
                fields[field] = data
            except:
                fields[field] = None
        return fields
    raise TypeError("Type %s not serializable" % type(obj))


def json_serial_report(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj.__class__, DeclarativeMeta):
        fields = {}
        for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
            if field in ['query', 'registry']:
                continue
            try:
                data = obj.__getattribute__(field)
                json.dumps(data, default=json_serial)
                fields[field] = data
            except:
                fields[field] = None
        return fields
    raise TypeError("Type %s not serializable" % type(obj))


def get_script_dir(follow_symlinks=True):
    if getattr(sys, 'frozen', False):
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)


def get_error(error_text, status=200):
    res = {
        'status': 'error',
        'message': error_text
    }
    return Response(
        response=json.dumps(res, ensure_ascii=False),
        mimetype='application/json',
        status=status
    )


def get_answer(text, info=None):
    if info is None:
        info = {}
    res = {
        'status': 'ok',
        'message': text
    }
    answer = {**res, **info}
    return Response(
        response=json.dumps(answer, ensure_ascii=False, default=json_serial),
        mimetype='application/json',
        status=200,
    )


def compare_days(one: datetime.datetime, two: datetime.datetime):
    if one.year == two.year and one.month == two.month and one.day == two.day:
        return True
    return False


def get_random_string(length):
    string = ''.join(random.choice(ascii_lowercase) for i in range(length))
    return string


def get_norm_word(word, digit):
    morph = pymorphy3.MorphAnalyzer()
    norm_word = morph.parse(word)[0]
    return norm_word.make_agree_with_number(digit).word


def compare_date(one: datetime.datetime, two: datetime.datetime):
    if one.day == two.day and one.month == two.month and one.year == two.year:
        return True
    else:
        return False


def compare_date_full(one: datetime.datetime, two: datetime.datetime):
    if one.day == two.day and one.month == two.month and one.year == two.year and one.hour == two.hour and one.minute == two.minute:
        return True
    else:
        return False


def get_phone_region(phone) -> Union[str, None]:
    url = 'http://num.voxlink.ru/get/'

    params = {
        'num': '+7' + phone
    }

    try:
        response = requests.get(url, params=params)

        data = response.json()['region']
        return data
    except:
        return None


def is_moscow_str(text: str) -> bool:
    if isinstance(text, str) is False:
        return False
    if 'Москва' in text or 'Московская' in text:
        return True
    return False