from flask import blueprints, session, request, abort, redirect, render_template, send_file
from errors import *
import chat.processing
import traceback
import json
import bot
import chat


app = blueprints.Blueprint('avito_new', __name__, url_prefix='/kek/avito_new')


@app.route('/', methods=['POST', 'GET'])
def callback():
    data = request.json 
#    return 'OK'
    try:
        bot.send_message('[NEW] Получен вебхук:\n{}'.format(json.dumps(data, ensure_ascii=False, indent=3)))
    except:
        pass

    try:
        # chat.chat(1, data)
        chat.processing.avito_chat(data, True)
    except:
        print(traceback.format_exc())
    return 'OK', 200
