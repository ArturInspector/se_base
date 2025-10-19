import traceback

from telebot import TeleBot
from telebot.types import Message
import config
import notifications.api


tg_bot = TeleBot(config.Production.NOTIFICATIONS_BOT_TOKEN)
gruz_bot = TeleBot('6035133080:AAFcZQ0fHN7p4toYDywIjaeG5u1ytMygqSA')


@tg_bot.message_handler()
def in_message(message: Message):
    print(message)
    tg_id = message.chat.id
    tg_user = notifications.api.get_user_by_tg_id(tg_id)
    if tg_user is None:
        if message.text != config.Production.BOT_PASSWORD:
            tg_bot.send_message(tg_id, 'Введите пароль')
            return
        else:
            notifications.api.create_tg_user(tg_id)
            tg_bot.send_message(tg_id, 'Вы зарегистрированы\nОжидайте сообщений')
    else:
        tg_bot.send_message(tg_id, 'Ожидайте сообщений')


def send_message(text, audio=None):
    tg_users = notifications.api.get_users()
    for user in tg_users:
        try:
            if audio is None:
                tg_bot.send_message(user.tg_id, text, disable_web_page_preview=True)
            else:
                tg_bot.send_audio(user.tg_id, audio=audio, caption=text)
        except:
            traceback.format_exc()
            continue


def gruz_message(text, audio=None):
    try:
        if audio is None:
            gruz_bot.send_message(-1001944476439, text, disable_web_page_preview=True)
        else:
            gruz_bot.send_audio(-1001944476439, audio=audio, caption=text)
    except:
        traceback.format_exc()


def start_polling():
    while True:
        print('bot started')
        try:
            tg_bot.polling(none_stop=True, allowed_updates=["my_chat_member", "chat_member", "chat_join_request", "message"])
        except:
            continue
