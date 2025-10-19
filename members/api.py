from db import Session
from errors import *
from .entities import *
from uuid import uuid4
import bot
import utils
import cities
import traceback
import links
import chat


def get_members_by_avito_chat_id(avito_chat_id, session=None):
    if session is None:
        with Session() as session:
            members_list = session.query(Member).filter(Member.avito_chat_id == avito_chat_id).all()
    else:
        members_list = session.query(Member).filter(Member.avito_chat_id == avito_chat_id).all()
    return members_list


def get_members_by_city_id(city_id, session=None):
    if session is None:
        with Session() as session:
            members_list = session.query(Member).filter(Member.city_id == city_id).all()
    else:
        members_list = session.query(Member).filter(Member.city_id == city_id).all()
    return members_list


def get_member_by_id(member_id, session=None):
    if session is None:
        with Session() as session:
            member = session.query(Member).get(member_id)
    else:
        member = session.query(Member).get(member_id)
    return member


def get_member_by_phone(phone, session=None) -> Member:
    if session is None:
        with Session() as session:
            member = session.query(Member).filter(Member.phone == phone).order_by(Member.id.desc()).first()
    else:
        member = session.query(Member).filter(Member.phone == phone).order_by(Member.id.desc()).first()
    try:
        if member.source_id != 2:
            member.source_id = 2
    except:
        pass
    return member


def get_member_by_avito_chat_id(avito_chat_id, session=None):
    if session is None:
        with Session() as session:
            member = session.query(Member).filter(Member.avito_chat_id == avito_chat_id).first()
    else:
        member = session.query(Member).filter(Member.avito_chat_id == avito_chat_id).first()
    return member


def get_member_by_whatsapp_chat_id(whatsapp_chat_id, session=None):
    if session is None:
        with Session() as session:
            member = session.query(Member).filter(Member.whatsapp_chat_id == whatsapp_chat_id).first()
    else:
        member = session.query(Member).filter(Member.whatsapp_chat_id == whatsapp_chat_id).first()
    return member


def get_member_by_tg_id(tg_id, session=None):
    if session is None:
        with Session() as session:
            member = session.query(Member).filter(Member.tg_id == tg_id).first()
    else:
        member = session.query(Member).filter(Member.tg_id == tg_id).first()
    return member


def get_member_by_dialog_token(dialog_token, session=None):
    if session is None:
        with Session() as session:
            member = session.query(Member).filter(Member.dialog_token == dialog_token).first()
    else:
        member = session.query(Member).filter(Member.dialog_token == dialog_token).first()
    return member


def get_member_by_uuid(uuid, session=None):
    if session is None:
        with Session() as session:
            member = session.query(Member).filter(Member.uuid == uuid).first()
    else:
        member = session.query(Member).filter(Member.uuid == uuid).first()
    return member


def get_member_by_telegram_id(tg_id, session=None):
    if session is None:
        with Session() as session:
            member = session.query(Member).filter(Member.telegram_id == tg_id).first()
    else:
        member = session.query(Member).filter(Member.telegram_id == tg_id).first()
    return member


def get_members(session=None):
    if session is None:
        with Session() as session:
            members_list = session.query(Member).all()
    else:
        members_list = session.query(Member).all()
    return members_list


def get_member_events(member_id, session=None):
    if session is None:
        with Session() as session:
            events_list = session.query(MemberEvent).filter(MemberEvent.member_id == member_id).all()
    else:
        events_list = session.query(MemberEvent).filter(MemberEvent.member_id == member_id).all()
    return events_list


def create_member_from_avito(avito_chat_id, avito_user_id, avito_type=2, session=None):
    if session is None:
        with Session() as session:
            uuid = str(uuid4())
            member = Member(avito_chat_id=avito_chat_id, avito_user_id=avito_user_id, source_id=1, uuid=uuid,
                            avito_type=avito_type)
            session.add(member)
            session.flush()
            session.refresh(member)
            create_event(member.id, 'Пользователь создан. Источник Авито', session=session)
            session.commit()
        return get_member_by_uuid(uuid)
    else:
        uuid = str(uuid4())
        member = Member(avito_chat_id=avito_chat_id, avito_user_id=avito_user_id, source_id=1, uuid=uuid,
                        avito_type=avito_type)
        session.add(member)
        session.flush()
        session.refresh(member)
        create_event(member.id, 'Пользователь создан. Источник Авито', session=session)
        return member


def create_member_from_whatsapp(whatsapp_chat_id):
    with Session() as session:
        uuid = str(uuid4())
        member = Member(whatsapp_chat_id=whatsapp_chat_id, source_id=2, uuid=uuid, phone=utils.telephone(whatsapp_chat_id))
        session.add(member)
        session.commit()
    member = get_member_by_uuid(uuid)
    create_event(member.id, 'Пользователь создан. Источник WhatsApp')
    return member


def create_member_from_telegram(tg_id, source_code=None):
    with Session() as session:
        uuid = str(uuid4())
        member = Member(tg_id=tg_id, source_id=3, uuid=uuid, source_code=source_code)
        session.add(member)
        session.commit()
    member = get_member_by_uuid(uuid)
    create_event(member.id, 'Пользователь создан. Источник Telegram')
    return member


def create_member_from_site(dialog_token):
    with Session() as session:
        uuid = str(uuid4())
        member = Member(dialog_token=dialog_token, source_id=4, uuid=uuid)
        session.add(member)
        session.commit()
    member = get_member_by_uuid(uuid)
    create_event(member.id, 'Пользователь создан. Источник стандарт-работа.рф')
    return member


def create_event(member_id, event, session=None):
    if session is None:
        with Session() as session:
            session.add(MemberEvent(member_id=member_id, event=event))
            session.commit()
    else:
        session.add(MemberEvent(member_id=member_id, event=event))


def set_name(member_id, name, member_, session=None):
    with Session() as session:
        member = get_member_by_id(member_id, session)
        if member is None:
            raise 'Пользователь не найден'
        member.name = name
        member.status = 1
        member.last_update = datetime.datetime.now()
        member_.name = name
        member_.status = 1
        create_event(member_id, 'Пользователь указал имя {}'.format(name), session)
        session.commit()


def set_member_name(member, name, session):
    member.name = str(name).capitalize()
    member.status = 1
    member.last_update = datetime.datetime.now()
    create_event(member.id, 'Пользователь указал имя {}'.format(name), session)


def set_age(member_id, age, member_):
    try:
        age = int(age)
    except:
        raise IncorrectDataValue('Напишите ваш возраст числом\n\nПример: 42')

    with Session() as session:
        member = get_member_by_id(member_id, session)
        if member is None:
            raise 'Пользователь не найден'

        if age < 18:
            member.is_ban = True
            session.commit()
            raise IncorrectDataValue('Извините, но ваш возраст не соответствует')
        if age >= 100:
            raise IncorrectDataValue('Укажите ваш настоящий возраст')

        member.age = age
        member.status = 2
        member.last_update = datetime.datetime.now()
        member_.age = age
        member_.status = 2
        create_event(member_id, 'Пользователь указал возраст {}'.format(age), session)
        session.commit()


def set_member_age(member, age, session):
    try:
        age = int(age)
    except:
        raise IncorrectDataValue('Напишите ваш возраст числом\n\nПример: 42')

    if age < 18:
        member.is_ban = True
        raise IncorrectDataValue('Извините, но ваш возраст не соответствует')
    if age >= 100:
        raise IncorrectDataValue('Укажите ваш настоящий возраст')

    member.age = age
    member.status = 2
    member.last_update = datetime.datetime.now()
    create_event(member.id, 'Пользователь указал возраст {}'.format(age), session)


def set_phone(member_id, phone, member_):
    try:
        phone = utils.telephone(phone)
    except:
        raise IncorrectDataValue('Напишите корректный номер телефона')
    if phone is None:
        raise IncorrectDataValue('Напишите корректный номер телефона')

    with Session() as session:
        member = get_member_by_id(member_id, session)
        if member is None:
            raise 'Пользователь не найден'
        member.phone = phone
        member.status = 3
        member.last_update = datetime.datetime.now()
        member_.phone = phone
        member_.status = 3
        create_event(member_id, 'Пользователь указал телефон +7{}'.format(phone), session)
        session.commit()


def set_member_phone(member, phone, session):
    try:
        phone = utils.telephone(phone)
    except:
        raise IncorrectDataValue('Напишите корректный номер телефона')
    if phone is None:
        raise IncorrectDataValue('Напишите корректный номер телефона')

    member.phone = phone
    member.status = 3
    member.last_update = datetime.datetime.now()
    create_event(member.id, 'Пользователь указал телефон +7{}'.format(phone), session)


def set_city(member_id, city, member_):
    city = cities.api.get_city(city)
    if city is None:
        raise IncorrectDataValue('Не удалось найти ваш город. Напишите, пожалуйста, ближайший крупный город')

    with Session() as session:
        member = get_member_by_id(member_id, session)
        if member is None:
            raise 'Пользователь не найден'
        member.city_id = city.id
        member.status = 4
        member.last_update = datetime.datetime.now()
        member_.city_id = city.id
        member_.status = 4
        create_event(member_id, 'Пользователь указал город {}'.format(city.name), session)
        session.commit()


def set_member_city(member, city, session):
    city = cities.api.find_city(city, session=session)
    if city is None:
        raise IncorrectDataValue('Не удалось найти ваш город. Напишите, пожалуйста, ближайший крупный город')

    member.city_id = city.id
    member.status = 4
    member.last_update = datetime.datetime.now()
    create_event(member.id, 'Пользователь указал город {}'.format(city.name), session)


def set_true(member_id, message, member_):
    if message == 'да':
        with Session() as session:
            member = get_member_by_id(member_id, session)
            if member is None:
                raise 'Пользователь не найден'
            member.status = 5
            member.last_update = datetime.datetime.now()
            member_.status = 5
            create_event(member_id, 'Пользователь подтвердил корректность данных', session)
            session.commit()
    elif message == 'нет':
        with Session() as session:
            member = get_member_by_id(member_id, session)
            if member is None:
                raise 'Пользователь не найден'
            member.status = 0
            member.last_update = datetime.datetime.now()
            member_.status = 0
            create_event(member_id, 'Пользователь отклонил корректность данных', session)
            session.commit()
            raise IncorrectDataValue('Напишите ваше имя')
    else:
        raise IncorrectDataValue('Напишите "Да" или "Нет"')


def set_member_true(member, message, session):
    if message == 'да':
        member.status = 5
        member.last_update = datetime.datetime.now()
        create_event(member.id, 'Пользователь подтвердил корректность данных', session)
    elif message == 'нет':
        member.status = 0
        member.last_update = datetime.datetime.now()
        create_event(member.id, 'Пользователь отклонил корректность данных', session)
        raise IncorrectDataValue('Напишите ваше имя')
    else:
        raise IncorrectDataValue('Напишите "Да" или "Нет"')


def leave_group(tg_id):
    try:
        with Session() as session:
            member = get_member_by_telegram_id(tg_id, session)
            if member is None:
                print('member not found')
                return
            if member.status != 10:
                print('member not status')
                return
            member.status = 11
            member.last_update = datetime.datetime.now()
            print('member aga')
            session.commit()
    except:
        print(traceback.format_exc())


def get_graphic():
    statuses = {
        'Начал анкетирование': 0,
        'Указал имя': 0,
        'Указал возраст': 0,
        'Указал телефон': 0,
        'Указал город': 0,
        'Подтвердил данные': 0,
        'Получил ссылку': 0,
        'В группе': 0,
        'Покинул группу': 0,
        'Ожидает добавление города': 0,
        'Ошибка создания ссылки': 0,
    }
    sources = {'Avito': 0, 'WhatsApp': 0, 'Telegram': 0, 'стандарт-работа.рф': 0}

    members = get_members()

    for member in members:
        statuses[member.get_status()] += 1
        if member.source_id == 1:
            sources['Avito'] += 1
        elif member.source_id == 2:
            sources['WhatsApp'] += 1
        elif member.source_id == 3:
            sources['Telegram'] += 1
        elif member.source_id == 4:
            sources['стандарт-работа.рф'] += 1

    statuses_data = {
        'categories': [],
        'series': [{
          'name': 'Количество',
          'data': []
        }]
    }
    for status in statuses:
        statuses_data['categories'].append(status)
        statuses_data['series'][0]['data'].append(statuses[status])

    sources_data = {
        'series': [],
        'labels': []
    }
    for source in sources:
        sources_data['series'].append(sources[source])
        sources_data['labels'].append(source)
    return {'statuses': statuses_data, 'sources': sources_data}


def invite_members_to_city(city_id):
    with Session() as session:
        members_list = session.query(Member).filter(Member.city_id == city_id, Member.status == 15).all()

        for member in members_list:
            try:
                link = links.api.create_link(member.id)
            except Exception as e:
                bot.send_message('Не удалось создать ссылку пользователю {}\n{}'.format(
                    member.id, str(e)
                ))
                continue
            chat.send_message(member, chat.send_link(link))