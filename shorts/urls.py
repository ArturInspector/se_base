from flask import blueprints, session, request, abort, redirect, render_template, send_file, Response
from errors import *
import utils
import traceback
import shorts

app = blueprints.Blueprint('shorts', __name__, url_prefix='/kek/shorts')


@app.route('/create')
def create():
    user = utils.get_user(session)
    if user is None:
        return abort(404)

    name = request.values.get('name', '', str)
    link = request.values.get('link', '', str)

    try:
        shorts.api.create_short(name, link)
    except IncorrectDataValue as e:
        return utils.get_error(e.message)
    except Exception as e:
        return utils.get_error(str(e))

    return utils.get_answer('Ссылка успешно создана')