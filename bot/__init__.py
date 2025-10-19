from telebot import TeleBot
from telebot.types import Message
from telebot.types import ChatMemberUpdated
from errors import *
from .entities import TGMessage
import config
import bot.api
import cities
import utils
import links
import members
import traceback
import polls
import chat
import admins
import spam


tg_bot = TeleBot(config.Production.BOT_TOKEN)
# tg_bot = TeleBot(config.Production.BOT_TOKEN_TEST)

SOURCES_DICT = {}

# @tg_bot.poll_answer_handler()
# def poll_handler(event):
#     print(event)
#     try:
#         polls.api.create_answer(event)
#     except:
#         print(traceback.format_exc())


@tg_bot.poll_handler(lambda t: t)
def _poll_handler(event):
    polls.api.update_tg_poll(event)


@tg_bot.chat_member_handler()
def handler_new_member(event):
    event: ChatMemberUpdated
    print(event)
    status = event.new_chat_member.status

    if status not in ['left', 'kicked']:
        if event.invite_link is not None:
            invite_link = event.invite_link.invite_link
            tg_id = event.new_chat_member.user.id
            links.api.in_group(invite_link, tg_id)
            return
    else:
        tg_id = event.from_user.id
        print('leave', tg_id)
        members.api.leave_group(tg_id)


@tg_bot.my_chat_member_handler()
def my_chat_handler(event):
    event: ChatMemberUpdated
    status = event.new_chat_member.status
    print(event)

    if status in ['left', 'kicked']:
        print('kicked')
        cities.api.remove_group_ip(event.chat.title, event.chat.id)
    else:
        print('add')
        if event.new_chat_member.can_manage_chat is True:
            cities.api.set_group_id(event.chat.title, event.chat.id)


@tg_bot.message_handler()
def in_message(message: Message):
    print(message)
    tg_id = message.from_user.id

    if message.content_type == 'text':
        if message.chat.type == 'private':
            if message.text.startswith('/start'):
                arr = message.text.split()
                if len(arr) == 2:
                    SOURCES_DICT[str(tg_id)] = arr[1]
            elif message.text.startswith('/городназвание'):
                # Команда для тестирования получения города из объявления
                try:
                    ai_processor = AvitoAIProcessor()
                    
                    # Создаем тестовые данные объявления
                    test_ad_data = {
                        'url': 'https://www.avito.ru/krasnodar/predlozheniya_uslug/gruzchiki_na_chas_vyvoz_pereezdy_raznorabochiy_1234567890',
                        'item_id': 1234567890
                    }
                    
                    # Тестируем извлечение города
                    city = ai_processor.extract_city_from_message('тест', test_ad_data)
                    
                    response = f"🔍 Тест извлечения города:\n"
                    response += f"URL: {test_ad_data['url']}\n"
                    response += f"Извлеченный город: {city if city else 'НЕ НАЙДЕН'}\n"
                    response += f"Доступные города в прайс-листе: {list(ai_processor.pricing_data.get('cities', {}).keys())[:10] if ai_processor.pricing_data else 'НЕТ ДАННЫХ'}"
                    
                    tg_bot.send_message(tg_id, response)
                    return
                except Exception as e:
                    tg_bot.send_message(tg_id, f"❌ Ошибка при тестировании: {str(e)}")
                    return
            elif message.text.startswith('/городтест'):
                # Команда для тестирования с разными URL
                try:
                    from chat.ai import AvitoAIProcessor
                    ai_processor = AvitoAIProcessor()
                    
                    # Парсим URL из команды
                    parts = message.text.split(' ', 1)
                    if len(parts) > 1:
                        test_url = parts[1]
                    else:
                        test_url = 'https://www.avito.ru/moscow/predlozheniya_uslug/gruzchiki_na_chas_vyvoz_pereezdy_raznorabochiy_1234567890'
                    
                    # Создаем тестовые данные объявления
                    test_ad_data = {
                        'url': test_url,
                        'item_id': 1234567890
                    }
                    
                    # Тестируем извлечение города
                    city = ai_processor.extract_city_from_message('тест', test_ad_data)
                    
                    response = f"🔍 Тест извлечения города:\n"
                    response += f"URL: {test_ad_data['url']}\n"
                    response += f"Извлеченный город: {city if city else 'НЕ НАЙДЕН'}\n"
                    response += f"Доступные города в прайс-листе: {list(ai_processor.pricing_data.get('cities', {}).keys())[:10] if ai_processor.pricing_data else 'НЕТ ДАННЫХ'}\n\n"
                    response += f"💡 Использование: /городтест https://www.avito.ru/город/..."
                    
                    tg_bot.send_message(tg_id, response)
                    return
                except Exception as e:
                    tg_bot.send_message(tg_id, f"❌ Ошибка при тестировании: {str(e)}")
                    return
            elif message.text.startswith('/городapi'):
                # Команда для тестирования с реальным API Авито
                try:
                    from chat.ai import AvitoAIProcessor
                    import avito.api
                    ai_processor = AvitoAIProcessor()
                    
                    # Парсим item_id из команды
                    parts = message.text.split(' ', 1)
                    if len(parts) > 1:
                        item_id = parts[1]
                    else:
                        item_id = '1234567890'  # Тестовый ID
                    
                    response = f"🔍 Тест API Авито:\n"
                    response += f"Item ID: {item_id}\n\n"
                    
                    # Тестируем новый API
                    try:
                        item_details = avito.api.get_item_details(item_id)
                        if item_details and 'location' in item_details:
                            city_name = item_details['location'].get('city', {}).get('name', '')
                            response += f"✅ Новый API:\n"
                            response += f"Город из API: {city_name if city_name else 'НЕ НАЙДЕН'}\n"
                            response += f"Полные данные: {str(item_details)[:200]}...\n\n"
                        else:
                            response += f"❌ Новый API: Данные не получены\n\n"
                    except Exception as e:
                        response += f"❌ Новый API: Ошибка - {str(e)}\n\n"
                    
                    # Тестируем старый API
                    try:
                        old_data = avito.api.get_ad_by_id(item_id)
                        response += f"📊 Старый API:\n"
                        response += f"Результат: {str(old_data)[:200]}...\n\n"
                    except Exception as e:
                        response += f"❌ Старый API: Ошибка - {str(e)}\n\n"
                    
                    # Тестируем извлечение города
                    test_ad_data = {
                        'url': f'https://www.avito.ru/moscow/predlozheniya_uslug/gruzchiki_na_chas_vyvoz_pereezdy_raznorabochiy_{item_id}',
                        'item_id': item_id
                    }
                    
                    city = ai_processor.extract_city_from_message('тест', test_ad_data)
                    response += f"🏙️ Извлеченный город: {city if city else 'НЕ НАЙДЕН'}\n"
                    response += f"💡 Использование: /городapi 1234567890"
                    
                    tg_bot.send_message(tg_id, response)
                    return
                except Exception as e:
                    tg_bot.send_message(tg_id, f"❌ Ошибка при тестировании API: {str(e)}")
                    return
            chat.chat(3, TGMessage(message, SOURCES_DICT.get(str(tg_id))))
        else:
            admins_list = tg_bot.get_chat_administrators(message.chat.id)
            for admin in admins_list:
                if tg_id == admin.user.id:
                    admins.api.create_message(message)
                    return

            spam.processing(message)

    # tg_user = bot.api.get_user_by_tg_id(tg_id)
    # if tg_user is None:
    #     if message.text != config.Production.BOT_PASSWORD:
    #         tg_bot.send_message(tg_id, 'Введите пароль')
    #         return
    #     else:
    #         bot.api.create_tg_user(tg_id)
    #         tg_bot.send_message(tg_id, 'Вы зарегистрированы\nОжидайте сообщений')
    # else:
    #     tg_bot.send_message(tg_id, 'Ожидайте сообщений')


def get_group_info(group_id):
    try:
        res = tg_bot.get_chat(group_id)
    except:
        print(traceback.format_exc())
        res = None
    return res


def create_invite_link(city_id, link_name):
    city = cities.api.get_city_by_id(city_id)
    if city is None:
        send_message('Попытка создать ссылку в несуществующем городе\n\nID Города: {}'.format(city_id))
        raise IncorrectDataValue('Город не найден')
    if city.group_id is None:
        raise GroupNotAllowed()

    rand_str = utils.get_random_string(6)

    try:
        link = tg_bot.create_chat_invite_link(city.group_id, '{}_'.format(rand_str, link_name), member_limit=1)
        return link.invite_link
    except Exception as e:
        send_message('Не удалось создать пригласительную ссылку\n\nГород: {}\n\nLink Name: {}\n\nПричина{}'.format(
            city.name, link_name, str(e)
        ))
        raise IncorrectDataValue('Не удалось создать ссылку')


def send_message(text):
    tg_users = bot.api.get_users()
    for user in tg_users:
        try:
            tg_bot.send_message(user.tg_id, text)
        except:
            continue


def send_me(text, disable_web_page_preview=False):
    try:
        tg_bot.send_message(125350218, text, disable_web_page_preview=disable_web_page_preview)
    except:
        return


def send_me_audio(text, audio):
    try:
        tg_bot.send_audio(125350218, audio, caption=text)
    except:
        return


def send_msg(tg_id, text, audio=None):
    if audio is None:
        msg = tg_bot.send_message(chat_id=tg_id, text=text, disable_web_page_preview=True)
    else:
        msg = tg_bot.send_audio(tg_id, audio=audio, caption=text)
    return msg


def send_poll(chat_id, question, options, is_anonymous):
    msg = tg_bot.send_poll(
        chat_id=chat_id,
        question=question,
        options=options,
        is_anonymous=is_anonymous
    )
    return msg


def start_polling():
    while True:
        print('bot started')
        try:
            tg_bot.polling(
                none_stop=True,
                allowed_updates=["my_chat_member", "chat_member", "chat_join_request", "message", "poll_answer", "poll"],
                skip_pending=True
            )
        except:
            continue
