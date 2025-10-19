from flask import blueprints, session, request, abort, redirect, render_template, send_file
from errors import *
from .core import processing, get_report
import traceback
import json
import bot


app = blueprints.Blueprint('bitrix', __name__, url_prefix='/kek/bitrix')


@app.route('/', methods=['POST', 'GET'])
def callback():
    bot.send_me('#bitrx_test\n\nПолучен вебхук {}'.format(request.method))
    try:
        values_dict = {}
        for key in request.values:
            values_dict[key] = request.values[key]
        bot.send_me('#bitrx_test\n\n<code>{}</code>'.format(json.dumps(values_dict, ensure_ascii=False, indent=3)))
        processing(values_dict)
    except Exception as e:
        bot.send_me('Не удалось обработать вебхук\n{}'.format(str(e)))
        bot.send_me(traceback.format_exc())

    return 'OK', 200


@app.route('/test', methods=['POST', 'GET'])
def test_callback():


    return 'OK', 200


@app.route('/report')
def report():
    get_report()
    return 'OK', 200
