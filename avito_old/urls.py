from flask import blueprints, session, request, abort, redirect, render_template, send_file
from errors import *
import chat.processing
import traceback
import json
import bot


app = blueprints.Blueprint('avito_old', __name__, url_prefix='/kek/avito_old')


@app.route('/', methods=['POST', 'GET'])
def callback():
    data = request.json 

    try:
        bot.send_message('[OLD]: Получен вебхук:\n{}'.format(json.dumps(data, ensure_ascii=False, indent=3)))
    except:
        pass

    try:
        chat.processing.avito_chat(data, is_new=False)
    except Exception as e:
        print(traceback.format_exc())
        bot.send_message(f'[OLD AVITO] Ошибка обработки:\n{str(e)}')
    return 'OK', 200
