from flask import blueprints, session, request, abort, redirect, render_template, send_file
from errors import *
import traceback
import utils
import json
import chat
import bot


app = blueprints.Blueprint('whatsapp', __name__, url_prefix='/kek/whatsapp')


@app.route('/', methods=['POST', 'GET'])
def callback():
    data = request.json

    messages = data.get('messages')
    if messages is not None:
        for message in messages:
            try:
                print('go to ')
                print(message)
                chat.chat(2, message)
            except:
                print(traceback.format_exc())
    bot.send_me(json.dumps(data, ensure_ascii=False, indent=3))
    return 'OK', 200
