from typing import Union
from enum import Enum
import utils
import recalls.bitrix
import avito
import avito_old
import avito_new
import datetime

phone_arr = ['позвонить', 'телеф', 'номер', 'сотовый', 'звон']
telegram_arr = ['телеграм', 'teleg', 'телег', 'тг']
whatsapp_arr = ['whats', 'ватс', 'вац']


class SourceTypes(Enum):
    phone = 1
    telegram = 2
    whatsapp = 3


class Lead:
    def __init__(self, avito_chat_id, avito_type, message):
        self.avito_id = avito_chat_id
        self.avito_type = avito_type
        self.phone = None
        self.bitrix_deal_id = None
        self.message = message

        self.processing(self.message)

    def processing(self, text: str):
        if self.phone is None:
            self.phone = self.get_phone_number(text)

        if self.bitrix_deal_id is None:
            if self.phone is not None:
                if self.avito_type != 3:
                    self.bitrix_deal_id = recalls.bitrix.create_deal_from_avito(
                        phone=self.phone,
                        username='AvitoUser',
                        source_description='Avito: {}'.format(self.message)
                    )
                else:
                    self.bitrix_deal_id = recalls.bitrix.create_deal_from_avito_stream(
                        phone=self.phone,
                        username='AvitoUser',
                        source_description='Avito: {}'.format(self.message)
                    )
        else:
            return 


        if self.avito_type != 3:
            if self.phone is None:
                # ВСЕГДА используем ИИ для генерации ответа
                try:
                    from chat.ai import SmartAIAssistant
                    ai_processor = SmartAIAssistant()
                    text = ai_processor.process_message(self.message, self.avito_id)
                except Exception as e:
                    # Fallback на ИИ fallback без шаблонов
                    try:
                        text = ai_processor._get_fallback_response(self.message)
                    except:
                        text = "Здравствуйте! Укажите город, количество грузчиков и время работы для расчета стоимости."
            else:
                text = "Спасибо, мы Вам перезвоним!"
        else:
            if self.phone is None:
                now = datetime.datetime.now()
                if now.hour >= 20 or now.hour < 8:
                    text = """Здравствуйте!

К сожалению мы на связи с 8:00-20:00 (мск) 
Напишите номер телефона и как только приедем в офис перезвоним Вам и назовем цену которая устроит Вас"""
                else:
                    text = """Здравствуйте!

Чтобы точно написать стоимость работ 
Напишите пожалуйста свой номер телефона, мы перезвоним в течение 5-ти минут. 📲"""
            else:
                now = datetime.datetime.now()
                if now.hour >= 20 or now.hour < 8:
                    text = """Спасибо, что написали номер телефона, к сожалению мы работаем с 8:00-20:00 по Мск 
Мы перезвоним Вам.📲⏱"""
                else:
                    text = """Спасибо, ожидайте мы вам позвоним"""

        if self.avito_type == 1:
            avito_old.api.send_message(self.avito_id, text)
        elif self.avito_type == 2:
            avito.api.send_message(self.avito_id, text)
        elif self.avito_type == 3:
            avito_new.api.send_message(self.avito_id, text)

    @staticmethod
    def get_phone_number(text: str) -> Union[str, None]:
        return utils.telephone(text)

    @staticmethod
    def get_source_type(text: str) -> Union[SourceTypes, None]:
        text = text.lower()

        for phone_str in phone_arr:
            if phone_str in text:
                return SourceTypes.phone

        for tg_str in telegram_arr:
            if tg_str in text:
                return SourceTypes.telegram

        for whats_str in whatsapp_arr:
            if whats_str in text:
                return SourceTypes.whatsapp

        return None
