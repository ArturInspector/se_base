import traceback
from threading import Timer
import shortcuts.api
import members
import datetime
import callstats
import utils


def processing():
    try:
        members_list = members.api.get_members()
        tasks = shortcuts.api.get_tasks()
        now = datetime.datetime.now()

        if len(tasks) > 0:
            # for member in members_list:
            #     diff = now.timestamp() - member.last_update.timestamp()
            #     minutes = int(diff / 60)
            #
            #     for task in tasks:
            #         if member.status == task.member_status and minutes == task.minutes:
            #             try:
            #                 shortcuts.api.create_message(member.phone, task.message, False)
            #             except:
            #                 print(traceback.format_exc())

            for task in tasks:
                if task.member_status != -71:
                    continue
                calls_list = callstats.beeline.get_calls(now, '9272430323@ip.beeline.ru')

                for call in calls_list:
                    diff = now.timestamp() - call['startDate'] / 1000
                    minutes = int(diff / 60)
                    print('[Прошло минут {}] [Задача минут: {}] {}'.format(minutes, task.minutes, call))

                    if minutes == task.minutes and call['direction'] == 'OUTBOUND' and call['status'] == 'PLACED' and call['duration'] > 0:
                        check = shortcuts.api.get_message_by_phone(utils.telephone(call['phone_to']))
                        if check is not None:
                            continue
                        #shortcuts.api.create_message(call['phone_to'], task.message, is_business=True)

    except:
        print(traceback.format_exc())
    finally:
        Timer(60, processing).start()