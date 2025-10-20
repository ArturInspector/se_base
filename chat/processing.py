import logging

from .models import *
from errors import *
from db import Session
from .api import get_model
from .messages import *
from .ai import AvitoAIProcessor
import chat
import members
import chats_log
import avito
import config
import cache
import links
import datetime
import recalls
import avito_new
import avito_old
import traceback
import bot
import utils

logger = logging.getLogger(__name__)


RECALLS = {}

MOSCOW_BOT = 'https://t.me/se_registration_bot?start=avito'
ANOTHER_BOT = 'https://t.me/se_rabota_bot'

MOSCOW_IDS = [
    7198751017,
    7198470978,
    4643410967,
    7198367320,
    4542971474,
    7198607829,
    4543211970,
    4542962968,
    4542942172,
    4543117867,
    4510609983,
    4382617614,
    4511489160,
    4447106486,
    4159441254,
    4543042569,
    4542557051,
    4510872435,
    4511254439,
    4510611983,
    4511130980,
    4159128886,
    4159516248,
    4543349730,
    4543154076,
]


def _get_dialogue_summary_for_bitrix(chat_id: str) -> str:
    """
    Получение краткого саммари диалога для Битрикса без зависимости от AI-процессора
    Принцип: Single Responsibility - только извлечение истории, без AI логики.
    Еблан который писал прошлый код - учись.
    """
    try:
        summary = chats_log.api.get_chat_summary(chat_id, max_messages=5)
        logger.debug(f"_get_dialogue_summary_for_bitrix: Саммари из БД: {summary[:50]}...")
        return summary
    except Exception as e:
        logger.error(f"_get_dialogue_summary_for_bitrix: Ошибка получения саммари: {e}")
        return "История недоступна"


def avito_chat(data, is_new=False):
    logger.debug(f"avito_chat: START")
    ai_processor = None
    ad_data = {}
    
    try:
        model = AvitoMessageModel.model_validate(data)
        
        if model.payload.value.type == 'system':
            logger.debug(f"avito_chat: Игнорируем системное сообщение")
            return
        
        if model.payload.value.author_id == model.payload.value.user_id:
            logger.debug(f"avito_chat: Игнорируем сообщение от бота")
            return
    except Exception as e:
        logger.error(f"avito_chat: Validation error: {e}")
        raise IncorrectDataValue('Ошибка валидации модели')

    if model.payload.value.author_id in [config.Production.AVITO_ID, config.Production.OLD_AVITO_ID, config.Production.NEW_AVITO_ID]:
        logger.debug(f"avito_chat: Пропускаем системное сообщение")
        return

    if cache.get_cache('avito', model.payload.value.id) is not None:
        logger.debug(f"avito_chat: Сообщение в кэше")
        with Session() as session:
            chats_log.api.create_chat_log(model, is_success=False, answer='None', comment='In cache',
                                          session=session)
            session.commit()
        return
    cache.set_cache('avito', model.payload.value.id, 1, ex=datetime.timedelta(minutes=10))

    # ЗАКОММЕНТИРОВАНО: Старая логика с шаблонами, заменена на AI
    # if is_new:
    #     avito_description = avito_new.api.get_category_by_ad_id(model.payload.value.item_id)
    #     if avito_description['id'] == 114:
    #         try:
    #             recall = RECALLS.get(model.payload.value.chat_id)
    #             if recall is None:
    #                 avito_type_id = 3
    #                 RECALLS[model.payload.value.chat_id] = recalls.Lead(model.payload.value.chat_id, avito_type_id,
    #                                                                     model.payload.value.content.text)
    #             else:
    #                 recall.processing(model.payload.value.content.text)
    #             return
    #         except:
    #             bot.send_message(traceback.format_exc())
    #             return

    try:
        chat_model = avito.api.get_chat(model.payload.value.chat_id)
        if model.payload.value.item_id is None and model.payload.value.type == 'system':
            model.payload.value.item_id = chat_model['context']['value']['id']
    except:
        chat_model = None

    # ОБРАБОТКА КОМАНД
    message_text = model.payload.value.content.text
    if message_text == '/городназвание':
        try:
            ai_processor = AvitoAIProcessor()
            ad_data = ai_processor.prepare_ad_data(
                item_id=model.payload.value.item_id,
                chat_id=model.payload.value.chat_id,
                user_id=model.payload.value.user_id,
                message=message_text
            )
            
            city = ai_processor.extract_city_from_message('тест', ad_data)
            response = f"🏙️ Город объявления: {city}" if city else "❌ Не удалось определить город объявления"
            
            if model.payload.value.user_id == config.Production.OLD_AVITO_ID:
                avito_old.api.send_message(model.payload.value.chat_id, response)
            elif model.payload.value.user_id == config.Production.AVITO_ID:
                avito.api.send_message(model.payload.value.chat_id, response)
            else:
                avito.api.send_message(model.payload.value.chat_id, response)
            
            logger.info(f"avito_chat: Команда /городназвание - город: {city}")
            return "OK"
            
        except Exception as e:
            logger.error(f"avito_chat: Ошибка команды /городназвание: {e}")
            error_response = f"❌ Ошибка при определении города: {str(e)}"
            if model.payload.value.user_id == config.Production.OLD_AVITO_ID:
                avito_old.api.send_message(model.payload.value.chat_id, error_response)
            elif model.payload.value.user_id == config.Production.AVITO_ID:
                avito.api.send_message(model.payload.value.chat_id, error_response)
            else:
                avito.api.send_message(model.payload.value.chat_id, error_response)
            return "OK"

    # ОПРЕДЕЛЕНИЕ ГОРОДА ОБЪЯВЛЕНИЯ И AI ОБРАБОТКА
    try:
        ai_processor = AvitoAIProcessor()
        
        ad_data = ai_processor.prepare_ad_data(
            item_id=model.payload.value.item_id,
            chat_id=model.payload.value.chat_id,
            user_id=model.payload.value.user_id,
            message=model.payload.value.content.text
        )
        
        final_city = ad_data.get('determined_city')
        logger.info(f"avito_chat: Город: {final_city}")
        
    except Exception as city_error:
        logger.error(f"avito_chat: Ошибка определения города: {city_error}")
        final_city = None
        ad_data = {}

    # AI с Function Calling сам создаст сделку в Битриксе когда получит телефон
    try:
        ad_data_with_city = ad_data.copy() if ad_data else {}
        if final_city:
            ad_data_with_city['determined_city'] = final_city
        
        ai_response = ai_processor.process_with_functions(
            message=model.payload.value.content.text,
            user_id=model.payload.value.author_id,
            ad_data=ad_data_with_city,
            chat_id=model.payload.value.chat_id,
            use_functions=True
        )
        logger.info(f"avito_chat: AI ответ сгенерирован")
        
        if model.payload.value.user_id == config.Production.OLD_AVITO_ID:
            send_result = avito_old.api.send_message(model.payload.value.chat_id, ai_response)
        elif model.payload.value.user_id == config.Production.AVITO_ID:
            send_result = avito.api.send_message(model.payload.value.chat_id, ai_response)
        else:
            send_result = avito.api.send_message(model.payload.value.chat_id, ai_response)
        
        logger.info(f"avito_chat: Сообщение отправлено: {send_result}")
        
        try:
            chats_log.api.create_chat_log(
                model, 
                is_success=True, 
                answer=ai_response, 
                comment='AI Response'
            )
        except Exception as log_error:
            logger.error(f"avito_chat: Ошибка логирования: {log_error}")
        
        return
        
    except Exception as e:
        logger.error(f'avito_chat: Ошибка AI обработки: {str(e)}')

        try:
            if ai_processor is None:
                ai_processor = AvitoAIProcessor()
            
            fallback_response = ai_processor._get_fallback_response(
                model.payload.value.content.text,
                ad_data
            )

            if model.payload.value.user_id == config.Production.OLD_AVITO_ID:
                avito_old.api.send_message(model.payload.value.chat_id, fallback_response)
            else:
                avito.api.send_message(model.payload.value.chat_id, fallback_response)
            
            logger.info(f"avito_chat: Fallback ответ отправлен")
        except Exception as inner_e:
            logger.error(f"avito_chat: Ошибка отправки fallback: {inner_e}")

        try:
            chats_log.api.create_chat_log(
                model,
                is_success=False,
                answer=fallback_response if 'fallback_response' in locals() else 'None',
                comment='AI Error Fallback'
            )
        except Exception as log_error:
            logger.error(f"avito_chat: Ошибка логирования: {log_error}")

    return

    # Казань отклик
    # if model.payload.value.item_id is not None:
    #     if model.payload.value.item_id == config.Production.KAZAN_ITEM_ID:
    #         _model = get_model()
    #         if len(_model.first_message) > 0:
    #             avito.api.send_message(model.payload.value.chat_id, _model.first_message)
    #         if len(_model.second_message) > 0:
    #             avito.api.send_message(model.payload.value.chat_id, _model.second_message)
    #         if len(_model.third_message) > 0:
    #             avito.api.send_message(model.payload.value.chat_id, _model.third_message)
    #
    #         chats_log.api.create_chat_log(model, is_success=True, answer='Отклик', comment='[Казань отклик]',
    #                                       session=session)
    #         session.commit()
    #         return
    #
    # return
        # member = members.api.get_member_by_avito_chat_id(
        #     avito_chat_id=model.payload.value.chat_id,
        #     session=session
        # )
        #
        # message = model.payload.value.content.text.lower()
        #
        # if member is None:
        #     if message == 'да':
        #         avito_type = 2
        #         member = members.api.create_member_from_avito(model.payload.value.chat_id, model.payload.value.user_id, avito_type, session=session)
        #         chat.send_message(member, NAME_REQUEST)
        #         chats_log.api.create_chat_log(model, is_success=True, answer=NAME_REQUEST, comment='Соискатель начал анкетирование', session=session)
        #         session.commit()
        #         return
        #     else:
        #         avito.api.send_message(model.payload.value.chat_id, HELLO_MESSAGE)
        #         chats_log.api.create_chat_log(model, is_success=True, answer=HELLO_MESSAGE,
        #                                       comment='Соискатель не начал анкетирование', session=session)
        #         session.commit()
        #         return
        # else:
        #     if member.is_ban:
        #         chat.send_message(member, 'Извините, но ваш возраст не подходит')
        #         chats_log.api.create_chat_log(model, is_success=True, answer='Извините, но ваш возраст не подходит',
        #                                       comment='Бан по возрасту', session=session)
        #         session.commit()
        #         return
        #
        #     if member.status == 0:
        #         members.api.set_member_name(member, message, session=session)
        #         chat.send_message(member, AGE_REQUEST)
        #         chats_log.api.create_chat_log(model, is_success=True, answer=AGE_REQUEST,
        #                                       comment='Соискатель указал имя', session=session)
        #     elif member.status == 1:
        #         try:
        #             members.api.set_member_age(member, message, session=session)
        #         except IncorrectDataValue as e:
        #             chat.send_message(member, e.message)
        #             chats_log.api.create_chat_log(model, is_success=True, answer=e.message, session=session)
        #         else:
        #             chat.send_message(member, PHONE_REQUEST)
        #             chats_log.api.create_chat_log(model, is_success=True, answer=PHONE_REQUEST, session=session)
        #     elif member.status == 2:
        #         try:
        #             members.api.set_member_phone(member, message, session=session)
        #         except IncorrectDataValue as e:
        #             chat.send_message(member, e.message)
        #             chats_log.api.create_chat_log(model, is_success=True, answer=e.message, session=session)
        #         else:
        #             chat.send_message(member, CITY_REQUEST)
        #             chats_log.api.create_chat_log(model, is_success=True, answer=CITY_REQUEST, session=session)
        #     elif member.status == 3:
        #         try:
        #             members.api.set_member_city(member, message, session=session)
        #         except IncorrectDataValue as e:
        #             chat.send_message(member, e.message)
        #             chats_log.api.create_chat_log(model, is_success=True, answer=e.message, session=session)
        #         else:
        #             text = check_info(member)
        #             chat.send_message(member, text)
        #             chats_log.api.create_chat_log(model, is_success=True, answer=text, session=session)
        #     elif member.status == 4:
        #         try:
        #             members.api.set_member_true(member, message, session=session)
        #         except IncorrectDataValue as e:
        #             chat.send_message(member, e.message)
        #             chats_log.api.create_chat_log(model, is_success=True, answer=e.message, session=session)
        #         else:
        #             try:
        #                 link = links.api.create_member_link(member, session=session)
        #             except IncorrectDataValue:
        #                 chat.send_message(member, 'Ожидайте, скоро мы вам пришлём ссылку на вступление в группу')
        #                 chats_log.api.create_chat_log(model, is_success=True, answer='Ожидайте, скоро мы вам пришлём ссылку на вступление в группу', session=session)
        #                 return
        #             except GroupNotAllowed:
        #                 chat.send_message(member, 'Ожидайте, скоро мы вам пришлём ссылку на вступление в группу')
        #                 chats_log.api.create_chat_log(model, is_success=True, answer='Ожидайте, скоро мы вам пришлём ссылку на вступление в группу', session=session)
        #                 return
        #             else:
        #                 chat.send_message(member, send_link(link))
        #
        #                 try:
        #                     member_city = cities.api.get_city_by_id(member.city_id)
        #                     if member.city_id not in [510, 787]:
        #                         if str(member_city.kladr).startswith('77') or str(member_city.kladr).startswith('50'):
        #                             msk_link = links.api.create_moscow_link(member.id)
        #                             if msk_link is not None:
        #                                 chat.send_message(member, send_moscow_link(msk_link))
        #                         if str(member_city.kladr).startswith('47'):
        #                             spb_link = links.api.create_spb_link(member.id)
        #                             if spb_link is not None:
        #                                 chat.send_message(member, send_spb_link(spb_link))
        #                 except:
        #                     pass
        #     elif member.status in [11, 15, 16]:
        #         try:
        #             link = links.api.create_member_link(member, session=session)
        #         except IncorrectDataValue:
        #             chat.send_message(member, 'Ожидайте, скоро мы вам пришлём ссылку на вступление в группу')
        #             chats_log.api.create_chat_log(model, is_success=True, answer='Ожидайте, скоро мы вам пришлём ссылку на вступление в группу', session=session)
        #         except GroupNotAllowed:
        #             chat.send_message(member, 'Ожидайте, скоро мы вам пришлём ссылку на вступление в группу')
        #             chats_log.api.create_chat_log(model, is_success=True,
        #                                           answer='Ожидайте, скоро мы вам пришлём ссылку на вступление в группу',
        #                                           session=session)
        #             return
        #
        #         chat.send_message(member, send_link(link))
        #     session.commit()
