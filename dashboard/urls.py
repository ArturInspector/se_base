from flask import blueprints, request, render_template, session, abort, redirect, url_for
from errors import *
from threading import Thread
from members.entities import Member
import traceback
import datetime
import avito
import utils
import members
import cities
import links
import polls
import users
import shorts
import admins
import chat.api
import dialogs
import callstats
import callstats_yandex
import shortcuts
import spam


app = blueprints.Blueprint('dashboard', __name__, url_prefix='/dashboard')


@app.route('/')
def home():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.auth'))
    if user.login != 'admin':
        return redirect('/dashboard/reports')

    return render_template('home.html', user=user)


@app.route('/cities')
def cities_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.auth'))
    if user.login != 'admin':
        return redirect('/dashboard/reports')

    return render_template('cities.html', user=user)


@app.route('/shortcuts')
def shortcuts_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.auth'))
    if user.login != 'admin':
        return redirect('/dashboard/reports')

    messages_list = shortcuts.api.get_messages()
    print(messages_list)

    return render_template('shortcuts.html', user=user, messages_list=messages_list)


@app.route('/tasks')
def tasks_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.auth'))
    if user.login != 'admin':
        return redirect('/dashboard/reports')

    tasks_list = shortcuts.api.get_tasks()

    return render_template('tasks.html', user=user, tasks_list=tasks_list, Member=Member)


@app.route('/reports')
def reports_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.auth'))

    reports_list = callstats.get_reports()

    return render_template('reports.html', user=user, reports_list=reports_list)


@app.route('/report')
def report_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.auth'))

    report_id = request.values.get('id', 0, int)

    report = callstats.get_report_by_id(report_id)

    if report is None:
        return utils.get_error('not found')

    s_recalls_0_10 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes <= 10 and recall.is_success is True, report.recalls))
    f_recalls_0_10 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes <= 10 and recall.is_success is False, report.recalls))

    s_recalls_10_20 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 10 and recall.recall_minutes <= 20 and recall.is_success is True, report.recalls))
    f_recalls_10_20 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 10 and recall.recall_minutes <= 20 and recall.is_success is False, report.recalls))

    s_recalls_20_30 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 20 and recall.recall_minutes <= 30 and recall.is_success is True, report.recalls))
    f_recalls_20_30 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 20 and recall.recall_minutes <= 30 and recall.is_success is False, report.recalls))

    s_recalls_30_40 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 30 and recall.recall_minutes <= 40 and recall.is_success is True, report.recalls))
    f_recalls_30_40 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 30 and recall.recall_minutes <= 40 and recall.is_success is False, report.recalls))

    s_recalls_40_50 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 40 and recall.recall_minutes <= 50 and recall.is_success is True, report.recalls))
    f_recalls_40_50 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 40 and recall.recall_minutes <= 50 and recall.is_success is False, report.recalls))

    s_recalls_50_60 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 50 and recall.recall_minutes <= 60 and recall.is_success is True, report.recalls))
    f_recalls_50_60 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 50 and recall.recall_minutes <= 60 and recall.is_success is False, report.recalls))

    s_recalls_60 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 60 and recall.is_success is True, report.recalls))
    f_recalls_60 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 60 and recall.is_success is False, report.recalls))

    recalls_none = list(filter(lambda recall: recall.recall_minutes is None, report.recalls))

    return render_template('report.html', user=user, report=report, s_recalls_0_10=s_recalls_0_10,
                           f_recalls_0_10=f_recalls_0_10, len=len,
                           s_recalls_10_20=s_recalls_10_20, f_recalls_10_20=f_recalls_10_20,
                           s_recalls_20_30=s_recalls_20_30, f_recalls_20_30=f_recalls_20_30,
                           s_recalls_30_40=s_recalls_30_40, f_recalls_30_40=f_recalls_30_40,
                           s_recalls_40_50=s_recalls_40_50, f_recalls_40_50=f_recalls_40_50,
                           s_recalls_50_60=s_recalls_50_60, f_recalls_50_60=f_recalls_50_60,
                           s_recalls_60=s_recalls_60, f_recalls_60=f_recalls_60, recalls_none=recalls_none
                           )


@app.route('/reports_yandex')
def reports_yandex_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.auth'))

    reports_list = callstats_yandex.get_reports()

    return render_template('reports_yandex.html', user=user, reports_list=reports_list)


@app.route('/report_yandex')
def report_yandex_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.auth'))

    report_id = request.values.get('id', 0, int)

    report = callstats_yandex.get_report_by_id(report_id)

    if report is None:
        return utils.get_error('not found')

    s_recalls_0_10 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes <= 10 and recall.is_success is True, report.recalls))
    f_recalls_0_10 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes <= 10 and recall.is_success is False, report.recalls))

    s_recalls_10_20 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 10 and recall.recall_minutes <= 20 and recall.is_success is True, report.recalls))
    f_recalls_10_20 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 10 and recall.recall_minutes <= 20 and recall.is_success is False, report.recalls))

    s_recalls_20_30 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 20 and recall.recall_minutes <= 30 and recall.is_success is True, report.recalls))
    f_recalls_20_30 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 20 and recall.recall_minutes <= 30 and recall.is_success is False, report.recalls))

    s_recalls_30_40 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 30 and recall.recall_minutes <= 40 and recall.is_success is True, report.recalls))
    f_recalls_30_40 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 30 and recall.recall_minutes <= 40 and recall.is_success is False, report.recalls))

    s_recalls_40_50 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 40 and recall.recall_minutes <= 50 and recall.is_success is True, report.recalls))
    f_recalls_40_50 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 40 and recall.recall_minutes <= 50 and recall.is_success is False, report.recalls))

    s_recalls_50_60 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 50 and recall.recall_minutes <= 60 and recall.is_success is True, report.recalls))
    f_recalls_50_60 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 50 and recall.recall_minutes <= 60 and recall.is_success is False, report.recalls))

    s_recalls_60 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 60 and recall.is_success is True, report.recalls))
    f_recalls_60 = list(filter(lambda recall: recall.recall_minutes is not None and recall.recall_minutes > 60 and recall.is_success is False, report.recalls))

    recalls_none = list(filter(lambda recall: recall.recall_minutes is None, report.recalls))

    return render_template('report_yandex.html', user=user, report=report, s_recalls_0_10=s_recalls_0_10,
                           f_recalls_0_10=f_recalls_0_10, len=len,
                           s_recalls_10_20=s_recalls_10_20, f_recalls_10_20=f_recalls_10_20,
                           s_recalls_20_30=s_recalls_20_30, f_recalls_20_30=f_recalls_20_30,
                           s_recalls_30_40=s_recalls_30_40, f_recalls_30_40=f_recalls_30_40,
                           s_recalls_40_50=s_recalls_40_50, f_recalls_40_50=f_recalls_40_50,
                           s_recalls_50_60=s_recalls_50_60, f_recalls_50_60=f_recalls_50_60,
                           s_recalls_60=s_recalls_60, f_recalls_60=f_recalls_60, recalls_none=recalls_none
                           )


@app.route('/recalls')
def recalls_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.auth'))

    report_id = request.values.get('id', 0, int)
    _min = request.values.get('min', 0, int)
    _max = request.values.get('max', 0, int)
    is_success = request.values.get('is_success', 0, int)

    is_success = True if is_success == 1 else False

    report = callstats.get_report_by_id(report_id)

    if report is None:
        return utils.get_error('not found')

    if _min == 0 and _max == 0:
        recalls_list = report.recalls
    elif _min == -1 and _max == -1:
        recalls_list = list(filter(lambda recall: recall.recall_minutes is None, report.recalls))
    else:
        recalls_list = list(filter(lambda recall: recall.recall_minutes is not None and recall.is_success == is_success and recall.recall_minutes >= _min and recall.recall_minutes < _max, report.recalls))

    return render_template('recalls.html', user=user, report=report, recalls_list=recalls_list)


@app.route('/recalls_yandex')
def recalls_yandex_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.auth'))

    report_id = request.values.get('id', 0, int)
    _min = request.values.get('min', 0, int)
    _max = request.values.get('max', 0, int)
    is_success = request.values.get('is_success', 0, int)

    is_success = True if is_success == 1 else False

    report = callstats_yandex.get_report_by_id(report_id)

    if report is None:
        return utils.get_error('not found')

    if _min == 0 and _max == 0:
        recalls_list = report.recalls
    elif _min == -1 and _max == -1:
        recalls_list = list(filter(lambda recall: recall.recall_minutes is None, report.recalls))
    else:
        recalls_list = list(filter(lambda recall: recall.recall_minutes is not None and recall.is_success == is_success and recall.recall_minutes >= _min and recall.recall_minutes < _max, report.recalls))

    return render_template('recalls.html', user=user, report=report, recalls_list=recalls_list)


@app.route('/dialogs')
def dialogs_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.auth'))
    if user.login != 'admin':
        return redirect('/dashboard/reports')

    source_id = request.values.get('source_id', 0, int)
    utm_source = request.values.get('utm_source', '', str)
    utm_medium = request.values.get('utm_medium', '', str)
    utm_campaign = request.values.get('utm_campaign', '', str)

    dialogs_list = dialogs.api.get_dialogs()
    dialogs_list.sort(key=lambda dialog: dialog.id, reverse=True)

    utm_sources = []
    utm_mediums = []
    utm_campaigns = []

    for dialog in dialogs_list:
        if dialog.utm_source is not None and dialog.utm_source not in utm_sources:
            utm_sources.append(dialog.utm_source)
        if dialog.utm_medium is not None and dialog.utm_medium not in utm_mediums:
            utm_mediums.append(dialog.utm_medium)
        if dialog.utm_campaign is not None and dialog.utm_campaign not in utm_campaigns:
            utm_campaigns.append(dialog.utm_campaign)

    if source_id > 0:
        dialogs_list = list(filter(lambda dialog: dialog.source_id == source_id, dialogs_list))
    if len(utm_source) > 0:
        dialogs_list = list(filter(lambda dialog: dialog.utm_source == utm_source, dialogs_list))
    if len(utm_medium) > 0:
        dialogs_list = list(filter(lambda dialog: dialog.utm_medium == utm_medium, dialogs_list))
    if len(utm_campaign) > 0:
        dialogs_list = list(filter(lambda dialog: dialog.utm_campaign == utm_campaign, dialogs_list))

    return render_template('chats.html', user=user, dialogs_list=dialogs_list, Member=Member,
                           utm_sources=utm_sources, utm_mediums=utm_mediums, utm_campaigns=utm_campaigns,
                           source_id=source_id, utm_source=utm_source, utm_medium=utm_medium, utm_campaign=utm_campaign)


@app.route('/dialog/<string:dialog_token>')
def dialog_page(dialog_token):
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.auth'))
    if user.login != 'admin':
        return redirect('/dashboard/reports')

    dialog = dialogs.api.get_dialog_by_token(dialog_token)
    if dialog is None:
        return utils.get_error('dialog not found')

    return render_template('admin_chat.html', user=user, dialog_token=dialog.token)


@app.route('/cleaning')
def cleaning_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.auth'))
    if user.login != 'admin':
        return redirect('/dashboard/reports')

    cities_list = cities.api.get_cities()
    cities_list = list(filter(lambda city: city.group_id is not None, cities_list))
    cities_list.sort(key=lambda city: city.name)

    return render_template('cleaning.html', user=user, cities_list=cities_list)


@app.route('/member')
def member_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.auth'))
    if user.login != 'admin':
        return redirect('/dashboard/reports')

    member_id = request.values.get('id', 0, int)
    member = members.api.get_member_by_id(member_id)
    if member is None:
        return utils.get_error('member not found')

    events_list = members.api.get_member_events(member_id)
    city = cities.api.get_city_by_id(member.city_id)
    links_list = links.api.get_links_by_member_id(member_id)

    return render_template('member.html', user=user, member=member, events_list=events_list, links_list=links_list,
                           city=city)


@app.route('/auth', methods=['POST', 'GET'])
def auth():
    user = utils.get_user(session)
    if user is not None:
        return redirect(url_for('dashboard.home'))

    if request.method == 'GET':
        return render_template('auth.html')
    else:
        login = request.values.get('login', '', str)
        password = request.values.get('password', '', str)

        check_auth = users.api.auth(login, password, session)
        if check_auth is False:
            return utils.get_error('Неверный логин или пароль')
        return utils.get_answer('Вы успешно авторизованы')


@app.route('/avito')
def avito_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.home'))
    if user.login != 'admin':
        return redirect('/dashboard/reports')

    ads = avito.api.get_ads(111)
    return render_template('avito.html', user=user, ads=ads, str=str, len=len)


@app.route('/mailer', methods=['GET', 'POST'])
def mailer_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.home'))
    if user.login != 'admin':
        return redirect('/dashboard/reports')
    if request.method == 'GET':
        polls_list = polls.api.get_polls()
        return render_template('mailer.html', user=user, polls_list=polls_list, len=len, range=range)
    else:
        text = request.values.get('text', '', str)
        is_test = request.values.get('is_test', 1, int)
        password = request.values.get('password', '', str)

        if len(text) == 0:
            return utils.get_error('Укажите текст рассылки')

        if is_test != 0 and is_test != 1:
            return utils.get_error('Укажите тип')

        is_test = True if is_test == 1 else False

        if is_test is False:
            if password != 'password_for_mailer':
                return utils.get_error('Incorrect password')

        Thread(target=chat.api.send_mailer, args=(text, is_test)).start()
        return utils.get_answer('Рассылка запущена')


@app.route('/poll', methods=['POST'])
def poll_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.home'))
    if user.login != 'admin':
        return redirect('/dashboard/reports')

    data = request.json
    print(data)

    if data['is_test'] is False:
        if data['password'] != 'password_for_poll':
            return utils.get_error('Incorrect password')

    question = data['question']
    options = data['options']
    is_anonymous = data['is_anonymous']

    is_anonymous = True if is_anonymous == 1 else False
    Thread(target=polls.api.send_poll, args=(question, options, is_anonymous, data['is_test'])).start()
    return utils.get_answer('Рассылка запущена')


@app.route('/poll')
def get_poll_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.home'))
    if user.login != 'admin':
        return redirect('/dashboard/reports')

    poll_id = request.values.get('id', 0, int)

    poll = polls.api.get_poll_by_id(poll_id)
    return render_template('poll.html', user=user, poll=poll)


@app.route('/spam')
def spam_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.home'))
    if user.login != 'admin':
        return redirect('/dashboard/reports')

    model = spam.get_model()
    spam_words = ''

    for word in model.words:
        spam_words += '{}, '.format(word)
    if len(spam_words) > 0:
        spam_words = spam_words[:-2]

    blocks_list = spam.api.get_blocks()
    return render_template('spam.html', user=user, model=model, spam_words=spam_words, blocks_list=blocks_list)


@app.route('/shorts')
def shorts_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.home'))
    if user.login != 'admin':
        return redirect('/dashboard/reports')

    shorts_list = shorts.api.get_shorts_full()
    return render_template('shorts.html', user=user, shorts_list=shorts_list, len=len)


@app.route('/chatbot', methods=['POST', 'GET'])
def chatbot_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.home'))
    if user.login != 'admin':
        return redirect('/dashboard/reports')

    if request.method == 'GET':
        model = chat.api.get_model()
        return render_template('chatbot.html', user=user, model=model)
    else:
        model = chat.api.KazanModel.model_validate(request.json)
        chat.api.save_model(model)
        return utils.get_answer('Ok')


@app.route('/admins')
def admins_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.home'))

    min_date = request.values.get('min_date', '', str)
    max_date = request.values.get('max_date', '', str)

    if len(min_date) > 0:
        try:
            min_date = datetime.datetime.strptime(min_date, '%Y-%m-%dT%H:%M')
        except:
            min_date = None
    else:
        min_date = None

    if len(max_date) > 0:
        try:
            max_date = datetime.datetime.strptime(max_date, '%Y-%m-%dT%H:%M')
        except:
            max_date = None
    else:
        max_date = None

    admins_list = admins.api.get_admins(min_date, max_date)
    return render_template('admins.html', user=user, len=len, admins_list=admins_list, min_date=min_date,
                           max_date=max_date)


@app.route('/admin')
def admin_page():
    user = utils.get_user(session)
    if user is None:
        return redirect(url_for('dashboard.home'))
    if user.login != 'admin':
        return redirect('/dashboard/reports')

    tg_id = request.values.get('tg_id', 0, int)

    min_date = request.values.get('min_date', '', str)
    max_date = request.values.get('max_date', '', str)

    if len(min_date) > 0:
        try:
            min_date = datetime.datetime.strptime(min_date, '%Y-%m-%dT%H:%M')
        except:
            min_date = None
    else:
        min_date = None

    if len(max_date) > 0:
        try:
            max_date = datetime.datetime.strptime(max_date, '%Y-%m-%dT%H:%M')
        except:
            max_date = None
    else:
        max_date = None

    admin = admins.api.get_admin(tg_id, min_date, max_date)
    return render_template('admin.html', user=user, len=len, admin=admin, int=int, min_date=min_date,
                           max_date=max_date)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('dashboard.auth'))