from flask import blueprints, session, request, abort, redirect, render_template, send_file, Response, make_response
from errors import *
import utils
import traceback
import users
import messages
import dialogs

app = blueprints.Blueprint('dialogs', __name__, url_prefix='/kek/dialogs')


@app.route('/create', methods=['POST'])
def create():
    params = request.json
    data = {
        'source_id': params.get('source_id', None),
        'source_ident': params.get('source_ident', None),
        'utm_source': params.get('utm_source', None),
        'utm_medium': params.get('utm_medium', None),
        'utm_campaign': params.get('utm_campaign', None),
        'utm_content': params.get('utm_content', None),
        'utm_term': params.get('utm_term', None),
    }
    model = dialogs.CreateDialogModel(**data)

    try:
        dialog = dialogs.api.create_dialog(model)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        return utils.get_error(str(e))

    response = make_response(utils.get_answer('', {'dialog_token': dialog.token}))
    response.set_cookie('dialog_token', dialog.token)
    return response


@app.route('/get')
def get_dialog():
    dialog_token = request.values.get('dialog_token', '', str)

    dialog = dialogs.api.get_dialog_by_token(dialog_token)
    if dialog is None:
        return utils.get_error('Диалог не найден')

    messages_list = messages.api.get_messages_by_dialog_token(dialog_token)
    messages_list.sort(key=lambda m: m.date)

    return utils.get_answer('', {'dialog': dialog, 'messages': messages_list})


@app.route('/in', methods=['POST'])
def in_message():
    data = request.json
    dialog_token = data.get('dialog_token', '')
    text = data.get('text', '')

    try:
        message = messages.api.create_message(dialog_token, text, is_system=False)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        return utils.get_error(str(e))
    return utils.get_answer('', {'message': message})


@app.route('/adm', methods=['POST'])
def adm_message():
    data = request.json
    dialog_token = data.get('dialog_token', '')
    text = data.get('text', '')

    try:
        message = messages.api.create_message(dialog_token, text, is_system=True)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        return utils.get_error(str(e))
    return utils.get_answer('', {'message': message})