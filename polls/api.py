from sqlalchemy.orm.attributes import flag_modified
from .entities import *
from errors import *
from db import Session
from loguru import logger
import cities
import bot
import utils
import traceback
import time

logger.add('{}/polls/polls.log'.format(utils.get_script_dir()))


def send_poll(question, options, is_anonymous, is_test=True):
    if len(question) < 1:
        raise IncorrectDataValue('Укажите заголовок опроса')
    if len(question) > 300:
        raise IncorrectDataValue('Заголовок опроса не может быть длиннее 300 символов')

    if len(options) < 2:
        raise IncorrectDataValue('Укажите минимум два ответа')
    if len(options) > 10:
        raise IncorrectDataValue('Кол-во ответов не может быть больше 10')

    for option in options:
        if len(option) < 1 or len(option) > 100:
            raise IncorrectDataValue('Текст ответа должен быть от 1 до 100 символов')

    cities_list = cities.api.get_cities()
    if is_test:
        cities_list = list(filter(lambda city: city.is_test, cities_list))

    tg_ids = {}
    default_options = {}
    for option in options:
        default_options[option] = 0

    poll_id = None
    try:
        poll = Poll(question=question, options=options, is_anonymous=is_anonymous, tg_ids={})
        session = Session()
        session.add(poll)
        session.commit()
        poll_id = poll.id
        session.close()
        bot.send_message('Рассылка опроса {} завершена'.format(question))
    except:
        bot.send_message('Не удалось создать объект рассылки-опроса\nОшибка:\n{}'.format(
            traceback.format_exc()
        ))
        return

    for city in cities_list:
        try:
            poll = bot.send_poll(city.group_id, question, options, is_anonymous)
            logger.info('{} {}'.format(city.name, poll))
            tg_ids[str(city.id)] = poll.poll.id

            with Session() as session:
                tg_poll = TGPoll(poll_id=poll.poll.id, options=default_options,
                                 city_id=city.id, city_name=city.name, parent_id=poll_id)
                session.add(tg_poll)
                session.commit()
        except:
            logger.error('{} {}'.format(city.name, traceback.format_exc()))
        finally:
            time.sleep(0.3)


def update_tg_poll(event):
    with Session() as session:
        tg_poll = session.query(TGPoll).filter(TGPoll.poll_id == event.id).first()
        print('tg_poll', tg_poll)
        if tg_poll is None:
            return

        for option in event.options:
            tg_poll.options[option.text] = option.voter_count

        flag_modified(tg_poll, 'options')
        session.commit()
        print('updated')


def get_poll_by_id(poll_id):
    with Session() as session:
        poll = session.query(Poll).get(poll_id)
        tg_polls_list = session.query(TGPoll).all()

    tg_polls = list(filter(lambda tg_poll: tg_poll.parent_id == poll.id, tg_polls_list))
    poll.tg_polls = tg_polls

    poll.result = {}
    poll.percents = {}
    poll.count = 0

    for option in poll.options:
        poll.result[option] = 0
        poll.percents[option] = 0

    for tg_poll in tg_polls:
        for option in tg_poll.options:
            poll.result[option] += tg_poll.options[option]
            poll.count += tg_poll.options[option]

    for option in poll.result:
        try:
            poll.percents[option] = int(poll.result.get(option) * 100 / poll.count)
        except:
            poll.percents[option] = 0
    return poll


def get_polls():
    with Session() as session:
        polls_list = session.query(Poll).all()
        tg_polls_list = session.query(TGPoll).all()

    for poll in polls_list:
        tg_polls = list(filter(lambda tg_poll: tg_poll.parent_id == poll.id, tg_polls_list))
        poll.tg_polls = tg_polls

        poll.result = {}
        poll.percents = {}
        poll.count = 0

        for option in poll.options:
            poll.result[option] = 0
            poll.percents[option] = 0

        for tg_poll in tg_polls:
            for option in tg_poll.options:
                poll.result[option] += tg_poll.options[option]
                poll.count += tg_poll.options[option]

        for option in poll.result:
            try:
                poll.percents[option] = int(poll.result.get(option) * 100 / poll.count)
            except:
                poll.percents[option] = 0

    polls_list.sort(key=lambda poll: poll.create_date, reverse=True)
    return polls_list
