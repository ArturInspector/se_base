from flask import blueprints, session, request, abort, redirect, render_template, send_file
from errors import *
import chat.processing
import traceback
import json
# import bot  # Временно отключено
import chat


app = blueprints.Blueprint('avito', __name__, url_prefix='/kek/avito')


@app.route('/', methods=['POST', 'GET'])
def callback():
    print('=== AVITO WEBHOOK RECEIVED ===')
    data = request.json
    print(f"Data: {data}")
    
    # Логируем в файл
    with open('/root/pepsiai/avito_webhook.log', 'a') as f:
        f.write(f"Webhook received: {data}\n")

    # try:
    #     bot.send_message('Получен вебхук:\n{}'.format(json.dumps(data, ensure_ascii=False, indent=3)))
    # except:
    #     pass

    # chat_id = data['payload']['value']['chat_id']
    # if chat_id == 'u2i-lvlBR5WAJGTUo6aAFCzZtw':
    #     chat.processing.avito_chat(data, False)
    #     return 'OK', 200

    try:
       # chat.chat(1, data)
        print("Вызываем avito_chat...")
        print(f"Данные для avito_chat: {data}")
        result = chat.processing.avito_chat(data, False)
        print(f"avito_chat результат: {result}")
    except Exception as e:
        print(f"Ошибка в avito_chat: {e}")
        print(traceback.format_exc())
    return 'OK', 200
