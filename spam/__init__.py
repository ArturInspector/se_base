from telebot.types import Message
from .urls import app
from .models import *
import spam.api
import utils
import json
import bot
import traceback


def update_model(status: bool, words: str):
    words = [word.strip().lower() for word in words.split(',')]
    model = get_model()
    model.status = status
    model.words = words
    save_model(model)


def save_model(model: SpamFilterModel):
    path = get_path()
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(model.model_dump(), ensure_ascii=False, indent=3))


def get_model() -> SpamFilterModel:
    path = get_path()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
    except:
        save_model(SpamFilterModel())
        return get_model()

    return SpamFilterModel.model_validate(data)


def get_path():
    return '{}/spam/model.json'.format(utils.get_script_dir())


def unblock(chat_id, user_id):
    bot.tg_bot.unban_chat_member(chat_id, user_id)


def processing(message: Message):
    text = message.text
    if text is None or len(text) == 0:
        return

    text = text.lower()

    model = get_model()

    if model.status is False:
        return

    result_words = []

    for word in model.words:
        if len(word) == 0:
            continue
        if word in text:
            result_words.append(word)

    if len(result_words) > 0:
        try:
            bot.tg_bot.ban_chat_member(message.chat.id, message.from_user.id, revoke_messages=True)
        except:
            spam.api.create_block(message, result_words, False, traceback.format_exc().splitlines()[-1])
        else:
            spam.api.create_block(message, result_words, True)

        try:
            bot.tg_bot.delete_message(message.chat.id, message.id)
        except:
            pass