from flask import blueprints, session, request, abort, redirect, render_template, send_file
from errors import *
import traceback
import json
import bot
import chat


app = blueprints.Blueprint('avito_old', __name__, url_prefix='/kek/avito_old')


@app.route('/', methods=['POST', 'GET'])
def callback():
    data = request.json
#    return 'OK'
    print(data)

    try:
        bot.send_message('[OLD]: Получен вебхук:\n{}'.format(json.dumps(data, ensure_ascii=False, indent=3)))
    except:
        pass

    try:
        chat.chat(1, data, True)
    except:
        print(traceback.format_exc())
    return 'OK', 200
