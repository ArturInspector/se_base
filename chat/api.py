from loguru import logger
from errors import *
from .models import *
import time
import cities
import bot
import traceback
import utils
import json


def send_mailer(text, is_test=True):
    if is_test:
        city = cities.api.get_city_by_id(1119)
        bot.send_msg(city.group_id, text)
    else:
        cities_list = cities.api.get_cities()

        cities_list = list(filter(lambda city: city.id in [160, 783, 802], cities_list))

        for city in cities_list:
            try:
                if city.group_id is None:
                    continue
                msg = bot.send_msg(city.group_id, text)
                logger.info('[Mailer]: {} {}'.format(city.name, msg))
            except Exception as e:
                logger.error('[Mailer]: {} {}'.format(city.name, traceback.format_exc()))
                bot.send_message('Сообщение рассылки не отправлено в группу города {}\n{}\n{}'.format(
                    city.name, city.group_id, str(e)
                ))
                continue
            finally:
                time.sleep(0.3)


def get_model_path() -> str:
    return '{}/chat/model.json'.format(utils.get_script_dir())


def get_model() -> KazanModel:
    try:
        with open(get_model_path(), 'r', encoding='utf-8') as file:
            data = json.loads(file.read())

        return KazanModel.model_validate(data)
    except:
        save_model(KazanModel())
        return get_model()


def save_model(model: KazanModel):
    with open(get_model_path(), 'w', encoding='utf-8') as f:
        f.write(json.dumps(model.model_dump()))

