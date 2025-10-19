from flask import blueprints, session, request, abort, redirect, render_template, send_file, Response
from errors import *
import utils
import traceback
import json
import shortcuts

app = blueprints.Blueprint('shortcuts', __name__, url_prefix='/kek/shortcuts')


@app.route('/task/create', methods=['POST'])
def task_create():
    user = utils.get_user(session)
    if user is None:
        return abort(403)

    data = request.json

    try:
        member_status = int(data.get('member_status', 0))
        message = data.get('message', '')
        minutes = int(data.get('minutes', 0))
    except:
        return utils.get_error('Ошибка валидации')

    try:
        shortcuts.api.create_task_notify(member_status, minutes, message)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        return utils.get_error(str(e))

    return utils.get_answer('Уведомление добавлено')


@app.route('/task/remove')
def remove_task():
    user = utils.get_user(session)
    if user is None:
        return abort(403)

    task_id = request.values.get('id', 0, int)

    try:
        shortcuts.api.remove_task_notify(task_id)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        return utils.get_error(str(e))

    return utils.get_answer('Уведомление было удалено')


@app.route('/create', methods=['POST'])
def create_message():
    user = utils.get_user(session)
    if user is None:
        return abort(403)

    data = request.json

    try:
        phone = data.get('phone', '')
        message = data.get('message', '')
        is_business = int(data.get('is_business', 0))
    except:
        return utils.get_error('Ошибка валидации')

    is_business = True if is_business == 1 else False

    try:
        shortcuts.api.create_message(phone, message, is_business=is_business)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        return utils.get_error(str(e))

    return utils.get_answer('Сообщение добавлено в рассылку')


@app.route('/remove')
def remove_message():
    user = utils.get_user(session)
    if user is None:
        return abort(403)

    message_id = request.values.get('id', 0, int)

    try:
        shortcuts.api.remove_message(message_id)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        return utils.get_error(str(e))

    return utils.get_answer('Сообщение было удалено')


@app.route('/queue')
def queue_message():
    try:
        message = shortcuts.api.get_last_message()
    except:
        print(traceback.format_exc())
        return json.dumps({'status': 0, 'id': None}, ensure_ascii=False, indent=3)

    if message is None:
        return json.dumps({'status': 0, 'id': None}, ensure_ascii=False, indent=3)

    return json.dumps(message.to_shortcut_model(), ensure_ascii=False, indent=3)