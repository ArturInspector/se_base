from flask import blueprints, session, request, abort, redirect, render_template, send_file, Response
from errors import *
import utils
import traceback
import spam

app = blueprints.Blueprint('spam', __name__, url_prefix='/kek/spam')


@app.route('/model/update', methods=['POST'])
def model_update():
    user = utils.get_user(session)
    if user is None:
        return abort(404)

    status = request.values.get('status', 0, int)
    words = request.values.get('words', '', str)

    status = True if status == 1 else False

    try:
        spam.update_model(status, words)
    except Exception as e:
        return utils.get_error(str(e))

    return utils.get_answer('Сохранено')


@app.route('/unblock')
def unblock():
    user = utils.get_user(session)
    if user is None:
        return abort(404)

    chat_id = request.values.get('chat_id', 0, int)
    user_id = request.values.get('user_id', 0, int)

    try:
        spam.unblock(chat_id, user_id)
    except Exception as e:
        return utils.get_error(str(e))

    return utils.get_answer('Сохранено')