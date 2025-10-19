from flask import blueprints, session, request, abort, redirect, render_template, send_file, Response
from errors import *
import utils
import traceback
import users
import json
import members
import links

app = blueprints.Blueprint('members', __name__, url_prefix='/kek/members')


@app.route('/get')
def get():
    user = utils.get_user(session)
    if user is None:
        return abort(404)

    members_list = members.api.get_members()
    data = []
    for member in members_list:
        source_id = ''
        if member.source_id == 1:
            source_id = member.avito_chat_id
        elif member.source_id == 2:
            source_id = member.whatsapp_chat_id
        elif member.source_id == 3:
            source_id = member.tg_id
        elif member.source_id == 4:
            source_id = member.dialog_token
        data.append(
            [
                member.id,
                member.get_source(),
                member.create_date.strftime('%Y/%m/%d %H:%M'),
                member.phone,
                member.name,
                member.get_status(),
                source_id
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


@app.route('/data')
def data_page():
    user = utils.get_user(session)
    if user is None:
        return abort(404)
    return utils.get_answer('', {'data': members.api.get_graphic()})


@app.route('/link')
def get_link_page():
    kladr_id = request.values.get('kladr_id', 0, int)

    try:
        link = links.api.create_link_by_kladr_id(kladr_id)
    except IncorrectDataValue as e:
        return utils.get_error(e.message, status=500)
    except Exception as e:
        return utils.get_error(str(e), status=500)
    return utils.get_answer('', {'link': link})