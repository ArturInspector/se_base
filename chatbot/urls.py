from flask import blueprints, session, request, abort, redirect, render_template, send_file
from errors import *
import traceback
import json
import bot
import utils
import chatbot


app = blueprints.Blueprint('chatbot', __name__, url_prefix='/chatbot')


@app.route('/auth')
def start_auth():
    url = chatbot.auth.get_auth_url()
    return redirect(url)


@app.route('/auth_callback')
def callback_auth():
    code = request.values.get('code', '', str)

    access_token = chatbot.auth.get_access_token(code)
    return utils.get_answer('', {'access_token': access_token})
