from flask import blueprints, session, request, abort, redirect, render_template, send_file
from errors import *
import traceback
import json
import bot
import chat.processing


app = blueprints.Blueprint('avito_gruz', __name__, url_prefix='/kek/avito_gruz')


@app.route('/', methods=['POST', 'GET'])
def callback():
    data = request.json
    print(data)

    try:
        bot.send_message('[GRUZ]: Получен вебхук:\n{}'.format(json.dumps(data, ensure_ascii=False, indent=3)))
    except:
        pass

    try:
        # ✅ Используем новую архитектуру SimpleAIProcessor через avito_chat
        chat.processing.avito_chat(data, is_new=False)
    except Exception as e:
        print(traceback.format_exc())
        bot.send_message(f'[GRUZ AVITO] Ошибка обработки:\n{str(e)}')
    return 'OK', 200
