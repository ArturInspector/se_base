from flask import blueprints, session, request, abort, redirect, render_template, send_file, Response
from errors import *
import utils
import traceback
import users
import json
import cities

app = blueprints.Blueprint('cities', __name__, url_prefix='/kek/cities')


@app.route('/get')
def get():
    user = utils.get_user(session)
    if user is None:
        return abort(404)

    cities_list = cities.api.get_cities()
    data = []
    for city in cities_list:
        data.append(
            [
                city.id,
                city.name,
                '<span class="text-success">Бот подключен</span>' if city.group_id is not None else '<span class="text-danger">Бот не подключен</span>'
            ]
        )
    result = {
        'data': data
    }
    return Response(
        response=json.dumps(result, ensure_ascii=False, default=utils.json_serial),
        status=200,
        mimetype='application/json'
    )


@app.route('/list')
def get_cities_list():
    cities_list = cities.api.get_cities()
    return utils.get_answer('', {'cities': cities_list})
