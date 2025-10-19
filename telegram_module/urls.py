from flask import blueprints, session, request, abort, redirect, render_template, send_file, Response
from errors import *
import utils
import traceback
import json
import telegram

app = blueprints.Blueprint('tg', __name__, url_prefix='/kek/tg')


@app.route('/get')
def get():
    user = utils.get_user(session)
    if user is None:
        return abort(403)

    group_id = request.values.get('group_id', 0, int)

    try:
        city_model = telegram.get_city_model_by_group_id(group_id)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        print(traceback.format_exc())
        return utils.get_error(str(e))

    return utils.get_answer('', {'data': city_model.model_dump()})


@app.route('/get/txt')
def get_txt():
    user = utils.get_user(session)
    if user is None:
        return abort(403)

    group_id = request.values.get('group_id', 0, int)

    try:
        file_path = telegram.get_city_model_by_group_id_txt(group_id)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        print(traceback.format_exc())
        return utils.get_error(str(e))

    return send_file(file_path, as_attachment=True)


@app.route('/clear')
def clear_page():
    user = utils.get_user(session)
    if user is None:
        return abort(403)

    group_id = request.values.get('group_id', 0, int)

    try:
        city_model = telegram.clear_city_by_group_id(group_id)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        print(traceback.format_exc())
        return utils.get_error(str(e))

    return utils.get_answer('', {'data': city_model.model_dump()})