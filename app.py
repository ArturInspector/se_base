from flask import Flask, redirect, url_for, abort, render_template, request, make_response
from flask_socketio import SocketIO
from threading import Thread
from db import init_db
import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import users
import bot
import cities
import avito
import avito_old
import avito_new
import members
import dashboard
import whatsapp
import reports
import bitrix
import polls
import notifications
import report_bot
import shorts
# import telegram  # Временно отключено
import utils
import dialogs
import callstats
import datetime
import bitrix_repair
import shortcuts
import spam
import callstats_yandex
import chatbot
import avito_gruz
from dashboard.kpi_dashboard import kpi_dashboard_bp
init_db()

try:
    from chats_log.migrations import run_migrations
    logger.info("Running auto-migrations...")
    run_migrations()
    logger.info("✅ Migrations complete")
except Exception as e:
    logger.warning(f"Auto-migration warning: {e}")

app = Flask(__name__)
app.config.from_object(config.Production)
app.secret_key = 'k=00=r3wgjh4 gh423u9tg43ug 43ugbfu23tr23'
app.register_blueprint(avito.app)
app.register_blueprint(avito_old.app)
app.register_blueprint(avito_new.app)
app.register_blueprint(avito_gruz.app)
app.register_blueprint(dashboard.app)
app.register_blueprint(kpi_dashboard_bp)  # ← KPI Dashboard
app.register_blueprint(members.app)
app.register_blueprint(cities.app)
app.register_blueprint(whatsapp.app)
app.register_blueprint(reports.app)
app.register_blueprint(bitrix.app)
app.register_blueprint(shorts.app)
# app.register_blueprint(telegram.app)  # Временно отключено
app.register_blueprint(dialogs.app)
app.register_blueprint(shortcuts.app)
app.register_blueprint(spam.app)
app.register_blueprint(chatbot.app)

socketio = SocketIO(app)
socketio.on_namespace(dialogs.ClientSocket('/s/dialogs'))

# Thread(target=bot.start_polling).start()
# Thread(target=report_bot.start_polling).start()
# Thread(target=shortcuts.processing).start()

logger.info(" пуск регистрации Avito webhooks...")

if hasattr(avito_old.api, 'set_webhook'):
    Thread(target=avito_old.api.set_webhook).start()
    logger.info("✅ OLD_AVITO webhook запущен")

@app.route('/')
def home():
    dialog_token = request.cookies.get('dialog_token', '')
    if len(dialog_token) == 0:
        dialog_token = None
    return render_template('site_chat.html', dialog_token=dialog_token)


@app.route('/clear')
def clear():
    response = make_response(redirect('/'))
    response.delete_cookie('dialog_token')
    return response


@app.route('/report2259')
def report():
    callstats.get_report()
    callstats_yandex.get_report()
    return utils.get_answer('ok')


@app.route('/report_avito')
def report_avito():
    try:
        avito_old.api.mark_online()
    except:
        pass
    try:
        avito_gruz.api.mark_online()
    except:
        pass
    return utils.get_answer('ok')


@app.route('/repair_calls')
def repair_calls():
    now = datetime.datetime.now()
    try:
        bitrix_repair.repair_avito_status(now)
    except:
        pass
    try:
        bitrix_repair.repair_avito_status_new(now)
    except:
        pass
    return utils.get_answer('ok')


@app.route('/i/<string:link>')
def shorts_page(link):
    try:
        link = str(link).lower()
        short = shorts.api.get_short_by_link(link)
        if short is None:
            return abort(404)

        shorts.api.create_visit(link)
        return redirect('https://t.me/StandartExpressMembers_bot?start={}'.format(link))
    except:
        return abort(404)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=6767)
