from typing import Union
from threading import Thread
from db import Session
from .entities import *
from errors import *
import config
import requests
import json
# import bot  # Временно отключено из-за конфликта импортов
import members
import transliterate


def get_city_by_id(city_id, session=None):
    if session is None:
        with Session() as session:
            city = session.query(City).get(city_id)
    else:
        city = session.query(City).get(city_id)
    return city


def get_city_bt_group_id(group_id, session=None):
    if session is None:
        with Session() as session:
            city = session.query(City).filter(City.group_id == group_id).first()
    else:
        city = session.query(City).filter(City.group_id == group_id).first()
    return city


def get_city_by_group_id(group_id, session=None):
    if session is None:
        with Session() as session:
            city = session.query(City).filter(City.group_id == group_id).first()
    else:
        city = session.query(City).filter(City.group_id == group_id).first()
    return city


def get_city_by_kladr(kladr, session=None):
    if session is None:
        with Session() as session:
            city = session.query(City).filter(City.kladr == kladr).first()
    else:
        city = session.query(City).filter(City.kladr == kladr).first()
    return city


def get_city_by_fias(fias, session=None):
    if session is None:
        with Session() as session:
            city = session.query(City).filter(City.fias == fias).first()
    else:
        city = session.query(City).filter(City.fias == fias).first()
    return city


def get_cities(session=None):
    if session is None:
        with Session() as session:
            cities_list = session.query(City).all()
    else:
        cities_list = session.query(City).all()
    return cities_list


def get_address_by_dadata(address):
    headers = {
        'Authorization': 'Token {}'.format(config.Production.DADATA_API_KEY),
        'Content-Type': 'application/json',
        'X-Secret': '{}'.format(config.Production.DADATA_SECRET)
    }
    data = [address]
    result = requests.post(
        'https://cleaner.dadata.ru/api/v1/clean/address',
        data=json.dumps(data),
        headers=headers
    )
    fias_text = result.text
    res = json.loads(fias_text)
    if res[0]['result'] is None:
        return None
    return res[0]


def set_group_id(group_name, group_id):
    if '-' not in group_name:
        # bot.send_message('В названии группы должно быть "-"\nИзмените название группы {} и добавьте бота заново'.format(
        #     group_name
        # ))
        return
    city_block = str(group_name).split('-')
    city_name = str(city_block[1]).strip()

    city = get_city_chat(city_name)
    if city is None:
        # bot.send_message('Не удалось распознать город группы\n\nГруппа:\n\n{}\nID Группы:\n{}\n\n'
        #                  'Удалите бота, переименуйте группу и добавьте бота заново'.format(
        #     group_name, group_id
        # ))
        return
    with Session() as session:
        city = get_city_by_id(city.id, session)
        city_id = city.id

        city.group_id = group_id
        # bot.send_message('Группа добавлена\n\nГород:\n{}\n\nГруппа:\n{}\n\nID Группы:\n{}'.format(
        #     city.name, group_name, group_id
        # ))
        session.commit()
        Thread(target=members.api.invite_members_to_city, args=(city_id, )).start()


def remove_group_ip(group_name, group_id):
    with Session() as session:
        city = get_city_by_group_id(group_id, session)
        if city is None:
            return

        # bot.send_message('Бот удалён из группы\n\nГруппа:\n{}\n\nГород:\n{}'.format(group_name, city.name))
        city.group_id = None
        session.commit()


def find_city(city_name, session=None) -> Union[City, None]:
    if session is None:
        with Session() as session:
            result = session.execute("SELECT * FROM cities WHERE MATCH(name) AGAINST('{}' IN BOOLEAN MODE) LIMIT 1".format(city_name))
            result = result.fetchone()
            return get_city_by_id(result[0], session=session) if result is not None else None
    else:
        result = session.execute(
            "SELECT * FROM cities WHERE MATCH(name) AGAINST('{}' IN BOOLEAN MODE) LIMIT 1".format(
                city_name))
        result = result.fetchone()
        return get_city_by_id(result[0], session=session) if result is not None else None


def get_city(city_name, city_list=None, trans=False):
    # dictionary = enchant.Dict("ru_RU")
    if city_list is None:
        cities = get_cities()
    else:
        cities = city_list
    probably_cities = []

    if trans:
        city_name = transliterate.translit(city_name, 'ru')

    cities_names = str(city_name).lower().strip().split()
    i = 0
    for c_name in cities_names:
        res = c_name.split('-')
        if len(res) > 1:
            cities_names[i] = res[0]
            cities_names.append(res[1])
        i += 1

    for city in cities:
        current_city = str(city.name).lower()
        score = None
        for c_name in cities_names:
            if c_name in current_city:
                if score is None:
                    score = len(current_city) - len(c_name)
                else:
                    score -= len(current_city) - len(c_name)
        if score is None:
            continue
        probably_cities.append(
            {
                'city': city,
                'score': score
            }
        )

    probably_cities.sort(key=lambda city_row: city_row['score'])

    if len(probably_cities) == 0:
        return None
    return probably_cities[0]['city']


def get_city_chat(city_name, city_list=None, trans=False):
    # dictionary = enchant.Dict("ru_RU")
    if city_list is None:
        cities = get_cities()
    else:
        cities = city_list
    probably_cities = []

    if trans:
        city_name = transliterate.translit(city_name, 'ru')

    cities_names = str(city_name).lower().strip().split()
    i = 0
    for c_name in cities_names:
        res = c_name.split('-')
        if len(res) > 1:
            cities_names[i] = res[0]
            cities_names.append(res[1])
        i += 1

    for city in cities:
        current_city = str(city.name).lower()
        score = None
        for c_name in cities_names:
            if c_name in current_city:
                if score is None:
                    score = len(current_city) - len(c_name)
                else:
                    score -= len(current_city) - len(c_name)

                words = current_city.split()
                if c_name in words:
                    score += 50
        if score is None:
            continue
        probably_cities.append(
            {
                'city': city,
                'score': score
            }
        )

    probably_cities.sort(key=lambda city_row: city_row['score'], reverse=True)

    if len(probably_cities) == 0:
        return None
    return probably_cities[0]['city']