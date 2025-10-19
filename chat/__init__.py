from errors import *
from .messages import *
from bot.entities import TGMessage
from messages.entities import Message as SiteMessage
from .api import get_model
import members
import config
import avito
import avito_old
import whatsapp
import links
import bot
import recalls
import traceback
import messages
import utils


CHAT_IDS = []
OLD_CHAT_IDS = []
RECALLS = {}


def chat(source_id, data, is_old=False):
    if is_old is False:
        if len(CHAT_IDS) > 2000:
            CHAT_IDS.clear()
    else:
        if len(OLD_CHAT_IDS) > 2000:
            OLD_CHAT_IDS.clear()

    source_code = None
    avito_ad_id = None
    if source_id == 1:
        chat_id = data['payload']['value']['id']

        if is_old is False:
            if chat_id in CHAT_IDS:
                return
            CHAT_IDS.append(chat_id)
        else:
            if chat_id in OLD_CHAT_IDS:
                return
            OLD_CHAT_IDS.append(chat_id)
        try:
            avito_ad_id = data['payload']['value']['item_id']
        except:
            avito_ad_id = None
        avito_chat_id = data['payload']['value']['chat_id']
        # if avito_chat_id not in ['u2i-OGA3NPWfi4TAGqVqLP4aGg', 'u2i-Ifgl1z8248Cwrzo7fC8Arg']:
        #     return
        avito_user_id = data['payload']['value']['author_id']

        content_type = data['payload']['value']['type']
        message = data['payload']['value']['content']['text']
        message = str(message).lower()

        avito_message_type = data['payload']['value']['type']
        is_otklik = False
        if avito_message_type == 'system':
            if 'откликнулся' not in message and 'сохранились' not in message:
                return
            is_otklik = True

        if avito_user_id in [1, config.Production.AVITO_ID, config.Production.OLD_AVITO_ID, config.Production.NEW_AVITO_ID] and is_otklik is False:
            return

        if (avito_ad_id == config.Production.KAZAN_ITEM_ID or (avito_ad_id is None and is_otklik)) and is_old is False:
            if avito_ad_id is None:
                ad_data = avito.api.get_chat(avito_chat_id)
                try:
                    avito_ad_id = ad_data['context']['value']['id']
                except:
                    pass
            if avito_ad_id == config.Production.KAZAN_ITEM_ID:
                model = get_model()
                if len(model.first_message) > 0:
                    avito.api.send_message(avito_chat_id, model.first_message)
                if len(model.second_message) > 0:
                    avito.api.send_message(avito_chat_id, model.second_message)
                if len(model.third_message) > 0:
                    avito.api.send_message(avito_chat_id, model.third_message)
                return

        # if content_type != 'text':
        #     avito.api.send_message(avito_chat_id, 'Пожалуйста, напишите текстом')
        #     print('2222')
        #     return
        # if len(message) == 0:
        #     print('333')
        #     avito.api.send_message(avito_chat_id, 'Пожалуйста, напишите текстом')
        #     return
        member = members.api.get_member_by_avito_chat_id(avito_chat_id)
    elif source_id == 2:
        print(data)
        msg_id = data['id']
        if msg_id in CHAT_IDS:
            return
        CHAT_IDS.append(msg_id)

        chat_id = data['chat_id']

        # if chat_id not in ['79518660560@c.us', '79270319515@c.us']:
        #     return

        chat_type = data['type']
        from_me = data['from_me']
        if chat_type != 'text':
            return
        if from_me:
            return

        message = data['text']['body']
        message = str(message).lower()

        if len(message) == 0:
            print('333')
            whatsapp.api.send_message(phone=utils.telephone(chat_id), text='Пожалуйста, напишите текстом')
            return
        member = members.api.get_member_by_phone(utils.telephone(chat_id))
    elif source_id == 3:
        data: TGMessage
        msg_id = data.msg_id
        if msg_id in CHAT_IDS:
            return
        CHAT_IDS.append(msg_id)

        chat_id = data.tg_id

        # if chat_id not in ['79518660560@c.us', '79270319515@c.us']:
        #     return

        message = data.text
        message = str(message).lower()
        source_code = data.source_code

        member = members.api.get_member_by_tg_id(chat_id)
    elif source_id == 4:
        data: SiteMessage
        msg_id = data.token
        if msg_id in CHAT_IDS:
            return
        CHAT_IDS.append(msg_id)

        chat_id = data.dialog_token

        # if chat_id not in ['79518660560@c.us', '79270319515@c.us']:
        #     return

        message = data.text
        message = str(message).lower()

        member = members.api.get_member_by_dialog_token(chat_id)
    else:
        raise IncorrectDataValue('Неизвестный тип источника')

    if member is None:
        avito_description = None
        if avito_ad_id is not None:
            avito_description = avito_old.api.get_category_by_ad_id(avito_ad_id)

        # ЗАКОММЕНТИРОВАНО: Старая логика с шаблонами, заменена на AI
        # if avito_description is not None and avito_description['id'] == 114:
        #     if is_old is False:
        #         return
        #     try:
        #         recall = RECALLS.get(avito_chat_id)
        #         if recall is None:
        #             avito_type_id = 2 if is_old is False else 1
        #             RECALLS[avito_chat_id] = recalls.Lead(avito_chat_id, avito_type_id, message)
        #         else:
        #             recall.processing(message)
        #         return
        #     except:
        #         bot.send_message(traceback.format_exc())
        #         return

        return
        if message == 'да':
            if source_id == 1:
                avito_type = 2 if is_old is False else 1
                member = members.api.create_member_from_avito(avito_chat_id, avito_user_id, avito_type)
                #avito.api.send_message(avito_chat_id, NAME_REQUEST)
                send_message(member, NAME_REQUEST)
                return
            elif source_id == 2:
                member = members.api.create_member_from_whatsapp(chat_id)
                whatsapp.api.send_message(phone=utils.telephone(chat_id), text=NAME_REQUEST)
            elif source_id == 3:
                member = members.api.create_member_from_telegram(chat_id, source_code)
                bot.send_msg(chat_id, NAME_REQUEST)
            elif source_id == 4:
                member = members.api.create_member_from_site(chat_id)
                messages.api.create_message(chat_id, NAME_REQUEST)
        else:
            print('12312', message)
            if source_id == 1:
                if is_old is False:
                    avito.api.send_message(avito_chat_id, HELLO_MESSAGE)
                else:
                    avito_old.api.send_message(avito_chat_id, HELLO_MESSAGE)
                return
            elif source_id == 2:
                whatsapp.api.send_message(phone=utils.telephone(chat_id), text=HELLO_MESSAGE)
                return
            elif source_id == 3:
                bot.send_msg(chat_id, HELLO_MESSAGE)
                return
            elif source_id == 4:
                messages.api.create_message(chat_id, HELLO_MESSAGE, buttons=HELLO_MESSAGE_BUTTONS)
                return
        return
    else:
        if member.is_ban:
            send_message(member, 'Извините, но ваш возраст не подходит')
            return

    return
    if member.status == 0:
        try:
            members.api.set_name(member.id, message, member)
        except IncorrectDataValue as e:
            send_message(member, e.message)
            return
        send_message(member, AGE_REQUEST)
        return
    elif member.status == 1:
        try:
            members.api.set_age(member.id, message, member)
        except IncorrectDataValue as e:
            send_message(member, e.message)
            return
        send_message(member, PHONE_REQUEST)
        return
    elif member.status == 2:
        try:
            members.api.set_phone(member.id, message, member)
        except IncorrectDataValue as e:
            send_message(member, e.message)
            return
        send_message(member, CITY_REQUEST)
        return
    elif member.status == 3:
        try:
            members.api.set_city(member.id, message, member)
        except IncorrectDataValue as e:
            send_message(member, e.message)
            return
        send_message(member, check_info(member), buttons=CHECK_INFO_BUTTONS)
        return
    elif member.status == 4:
        try:
            members.api.set_true(member.id, message, member)
        except IncorrectDataValue as e:
            send_message(member, e.message)
            return

        if member.source_id != 3:
            send_message(member, TELEGRAM_REQUEST, buttons=TELEGRAM_REQUEST_BUTTONS)
        else:
            try:
                link = links.api.create_link(member.id)
            except IncorrectDataValue:
                send_message(member, 'Ожидайте, скоро мы вам пришлём ссылку на вступление в группу')
                return
            except GroupNotAllowed:
                send_message(member, 'Ожидайте, скоро мы вам пришлём ссылку на вступление в группу')
                return

            send_message(member, send_link(link))

            try:
                member_city = cities.api.get_city_by_id(member.city_id)
                if member.city_id not in [510, 787]:
                    if str(member_city.kladr).startswith('77') or str(member_city.kladr).startswith('50'):
                        msk_link = links.api.create_moscow_link(member.id)
                        if msk_link is not None:
                            send_message(member, send_moscow_link(msk_link))
                    if str(member_city.kladr).startswith('47'):
                        spb_link = links.api.create_spb_link(member.id)
                        if spb_link is not None:
                            send_message(member, send_spb_link(spb_link))
            except:
                pass
        return
    elif member.status == 5:
        if message != 'далее':
            send_message(member, TELEGRAM_REQUEST, buttons=TELEGRAM_REQUEST_BUTTONS)
            return
        try:
            link = links.api.create_link(member.id)
        except IncorrectDataValue:
            send_message(member, 'Ожидайте, скоро мы вам пришлём ссылку на вступление в группу')
            return
        except GroupNotAllowed:
            send_message(member, 'Ожидайте, скоро мы вам пришлём ссылку на вступление в группу')
            return

        send_message(member, send_link(link))

        try:
            member_city = cities.api.get_city_by_id(member.city_id)
            if member.city_id not in [510, 787]:
                if str(member_city.kladr).startswith('77') or str(member_city.kladr).startswith('50'):
                    msk_link = links.api.create_moscow_link(member.id)
                    if msk_link is not None:
                        send_message(member, send_moscow_link(msk_link))
                if str(member_city.kladr).startswith('47'):
                    spb_link = links.api.create_spb_link(member.id)
                    if spb_link is not None:
                        send_message(member, send_spb_link(spb_link))
        except:
            pass
        return
    elif member.status in [11, 15, 16]: # ожидает добавления в группу (бот не добавлен)
        try:
            link = links.api.create_link(member.id)
        except IncorrectDataValue:
            send_message(member, 'Ожидайте, скоро мы вам пришлём ссылку на вступление в группу')
            return
        except GroupNotAllowed:
            send_message(member, 'Ожидайте, скоро мы вам пришлём ссылку на вступление в группу')
            return

        send_message(member, send_link(link))
        return


def send_message(member, message, auto_repeat=True, headers=None, buttons=[]):
    if member.source_id == 1:
        if member.avito_type == 1:
            return avito_old.api.send_message(member.avito_chat_id, message, auto_repeat, headers=headers)
        else:
            return avito.api.send_message(member.avito_chat_id, message, auto_repeat, headers=headers)

    elif member.source_id == 2:
        whatsapp.api.send_message(phone=utils.telephone(member.whatsapp_chat_id), text=message)
    elif member.source_id == 3:
        bot.send_msg(member.tg_id, message)
    elif member.source_id == 4:
        messages.api.create_message(member.dialog_token, message, buttons=buttons)
    else:
        return