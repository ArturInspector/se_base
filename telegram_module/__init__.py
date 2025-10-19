from .urls import app
from telethon import TelegramClient
from telethon.types import Channel
from telethon.types import User
from .models import *
from errors import *
from cities.entities import City
import config
import traceback
import cities
import bot
import utils
import asyncio

api_id = 2212521
api_hash = '633341c699031f3485956c9494867b9f'


async def get_city_model(group_id):
    async with TelegramClient('se_bot.session', api_id=api_id, api_hash=api_hash) as client:
        users_ids = []
        deleted_users = 0
        offline_users = 0
        users_count = 0

        group_entity = await client.get_entity(group_id)

        async for member in client.iter_participants(group_entity):
            users_count += 1
            member: User
            if member.is_self:
                continue
            if member.status is None:
                offline_users += 1
                if member.id not in users_ids:
                    users_ids.append(member.id)
            if member.deleted:
                deleted_users += 1
                if member.id not in users_ids:
                    users_ids.append(member.id)

    return CityModel(group_id=group_id, users_ids=users_ids, deleted_users=deleted_users, offline_users=offline_users,
                     users_count=users_count)


def get_city_model_by_group_id(group_id):
    loop = asyncio.new_event_loop()

    result = loop.run_until_complete(get_city_model(group_id))
    return result


async def get_city_model_txt(group_id):
    city = cities.api.get_city_by_group_id(group_id)
    if city is None:
        raise IncorrectDataValue('Город не найден')

    message = ''

    async with TelegramClient('se_bot.session', api_id=api_id, api_hash=api_hash) as client:

        group_entity = await client.get_entity(group_id)

        async for member in client.iter_participants(group_entity):
            member: User

            if member.is_self:
                continue
            if member.status is None:
                message += 'OFFLINE: TG_ID={} username={} first_name={} last_name={} last_online={}\n'.format(
                    member.id, member.username, member.first_name, member.last_name, member.status
                )
            if member.deleted:
                message += 'DELETED: TG_ID={} username={} first_name={} last_name={} last_online={}\n'.format(
                    member.id, member.username, member.first_name, member.last_name, member.status
                )

    file_path = '{}/reports/{}.txt'.format(utils.get_script_dir(), city.name)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(message)

    return file_path


def get_city_model_by_group_id_txt(group_id):
    loop = asyncio.new_event_loop()

    result = loop.run_until_complete(get_city_model_txt(group_id))
    return result


async def clear_city(group_id):
    city = cities.api.get_city_by_group_id(group_id)
    if city is None:
        raise IncorrectDataValue('Город не найден')

    async with TelegramClient('se_bot.session', api_id=api_id, api_hash=api_hash) as client:
        client: TelegramClient

        group_entity = await client.get_entity(group_id)

        async for member in client.iter_participants(group_entity):
            member: User

            if member.is_self:
                continue
            if member.status is None:
                try:
                    await client.kick_participant(group_entity, member)
                except:
                    print(traceback.format_exc())
                continue
            if member.deleted:
                print(member)
                try:
                    res = await client.kick_participant(group_entity, member)
                    print(res)
                except:
                    print(traceback.format_exc())
                continue


def clear_city_by_group_id(group_id):
    loop = asyncio.new_event_loop()

    loop.run_until_complete(clear_city(group_id))
    return get_city_model_by_group_id(group_id)
