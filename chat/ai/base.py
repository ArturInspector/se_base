import signal
import threading
from typing import Optional
import logging
import openai
import json

import config

from .extractors import CityExtractor, WorkDetailsExtractor
from .pricing import PricingCalculator
from .prompts import PromptBuilder
from .context import DialogueContextManager
from .config import DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, DEFAULT_TIMEOUT
from .functions import get_function_definitions
from .function_handlers import execute_function, format_function_result_for_ai

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[AVITO_BOT] %(levelname)s: %(funcName)s: %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class AvitoAIProcessor:
    AI_DISCLAIMER = "💬 Я AI-бот SE Express. "
    
    def __init__(self):
        logger.info("Инициализация AvitoAIProcessor")
        
        self.pricing_calculator = PricingCalculator()
        self.city_extractor = CityExtractor(self.pricing_calculator.pricing_data)
        self.work_extractor = WorkDetailsExtractor(self.city_extractor)
        self.prompt_builder = PromptBuilder(self.pricing_calculator.pricing_data)
        self.context_manager = DialogueContextManager()
        
        self.use_openai = self._init_openai_client()
    
    def _init_openai_client(self) -> bool:
        try:
            api_key = config.Production.OPENAI_API_KEY
            base_url = config.Production.OPENAI_BASE_URL
            
            if api_key.startswith('sk-1234') or len(api_key) < 20:
                logger.error("Обнаружен тестовый или невалидный OpenAI API ключ!")
                logger.error("Установите реальный API ключ в config.py")
                raise ValueError("Invalid API key - please set real API key in config.py")
            
            self.openai_client = openai.OpenAI(api_key=api_key, base_url=base_url)
            
            logger.info(f"OpenAI клиент инициализирован (base_url: {base_url})")
            
            test_response = self.openai_client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
                timeout=10
            )
            
            logger.info("OpenAI клиент успешно протестирован")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации OpenAI: {e}")
            self.openai_client = None
            return False
    
    def _call_openai_with_timeout(
        self, 
        messages: list,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        timeout: int = DEFAULT_TIMEOUT
    ) -> Optional[str]:
        result = [None]
        exception = [None]
        
        def api_call():
            try:
                response = self.openai_client.chat.completions.create(
                    model=DEFAULT_MODEL,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout
                )
                result[0] = response.choices[0].message.content
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=api_call)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout + 5)
        
        if thread.is_alive():
            logger.error("OpenAI API timeout")
            return None
        
        if exception[0]:
            logger.error(f"OpenAI API error: {exception[0]}")
            return None
        
        return result[0]
    
    def extract_city_from_message(self, message: str, ad_data: dict = None) -> Optional[str]:
        return self.city_extractor.extract_city_from_message(message, ad_data)
    
    def extract_work_details(self, message: str, ad_data: dict = None) -> dict:
        return self.work_extractor.extract_work_details(message, ad_data)
    
    def calculate_price(self, work_details: dict) -> Optional[str]:
        return self.pricing_calculator.calculate_price(work_details)
    
    def add_to_dialogue_context(self, chat_id: str, message: str, is_user: bool):
        self.context_manager.add_message(chat_id, message, is_user)
    
    def get_dialogue_summary(self, chat_id: str) -> str:
        return self.context_manager.get_dialogue_summary(chat_id)
    
    def prepare_ad_data(self, item_id: int, chat_id: str, user_id: int, message: str) -> dict:
        import avito
        import avito_old
        import re
        
        logger.debug(f"[AVITO_BOT]Подготовка ad_data для item_id={item_id}, chat_id={chat_id}")
        
        ad_data = {}
        
        if item_id:
            try:
                if hasattr(avito.api, 'get_item_details'):
                    item_details = avito.api.get_item_details(item_id)
                    if item_details and 'location' in item_details:
                        city_name = item_details['location'].get('city', {}).get('name', '')
                        if city_name:
                            logger.debug(f"Город из API: {city_name}")
                            ad_data = {
                                'city_from_api': city_name,
                                'item_id': item_id,
                                'location': item_details['location']
                            }
                
                if not ad_data:
                    if user_id == config.Production.OLD_AVITO_ID:
                        ad_data = avito_old.api.get_ad_by_id(item_id)
                    else:
                        ad_data = avito.api.get_ad_by_id(item_id)
                    logger.debug(f"Данные объявления из старого API")
                    
            except Exception as ad_error:
                logger.debug(f"Ошибка при получении данных объявления: {ad_error}")
        
        if not ad_data or 'error' in ad_data or 'url' not in ad_data:
            city_match = re.search(r'u2i-([^-]+)', chat_id)
            if city_match:
                city_slug = city_match.group(1)
                constructed_url = f"https://www.avito.ru/{city_slug}/predlozheniya_uslug/gruzchiki_na_chas_vyvoz_pereezdy_raznorabochiy_{item_id}"
                
                if not ad_data:
                    ad_data = {}
                ad_data['url'] = constructed_url
                logger.debug(f"Создан URL из chat_id: {constructed_url}")
            else:
                constructed_url = f"https://www.avito.ru/moscow/predlozheniya_uslug/gruzchiki_na_chas_vyvoz_pereezdy_raznorabochiy_{item_id}"
                if not ad_data:
                    ad_data = {}
                ad_data['url'] = constructed_url
                logger.debug(f"Создан дефолтный URL: {constructed_url}")
        
        ad_city = self.city_extractor.extract_city_from_message('', ad_data)
        logger.debug(f"Определен город объявления: {ad_city}")
        
        message_city = self.city_extractor.extract_city_from_message(message, ad_data)
        
        if message_city and message_city != ad_city:
            logger.debug(f"Клиент указал другой город: {message_city} (вместо {ad_city})")
            final_city = message_city
        else:
            final_city = ad_city
        
        if final_city:
            ad_data['determined_city'] = final_city
            logger.debug(f"Финальный город: {final_city}")
        
        return ad_data
    
    def process_message(self, message: str, user_id: int, ad_data: dict = None, chat_id: str = None) -> str:
        """
        Алиас для обратной совместимости.
        Вызывает process_with_functions с use_functions=True
        """
        return self.process_with_functions(
            message=message,
            user_id=user_id,
            ad_data=ad_data,
            chat_id=chat_id,
            use_functions=True
        )
    
    def _is_first_message(self, chat_id: str) -> bool:
        """Проверка: это первое сообщение в чате (через БД)?"""
        if not chat_id:
            return True
        
        try:
            from db import Session
            import chats_log
            with Session() as session:
                count = session.query(chats_log.entities.ChatLog).filter(
                    chats_log.entities.ChatLog.chat_id == chat_id,
                    chats_log.entities.ChatLog.is_success == True
                ).count()
                return count == 0
        except Exception as e:
            logger.error(f"Ошибка проверки is_first_message: {e}")
            return True
    
    def process_with_functions(
        self, 
        message: str, 
        user_id: int, 
        ad_data: dict = None, 
        chat_id: str = None,
        use_functions: bool = True
    ) -> str:
        """
        Обработка сообщения с поддержкой OpenAI Function Calling
        
        Args:
            message: Сообщение от клиента
            user_id: ID пользователя
            ad_data: Данные объявления (город, item_id и т.д.)
            chat_id: ID чата для истории
            use_functions: Включить function calling (по умолчанию True)
            
        Returns:
            str: Ответ для клиента
        """
        logger.info(f"[AVITO_BOT]Обработка с functions: '{message[:50]}...'")
        
        try:
            if chat_id:
                self.add_to_dialogue_context(chat_id, message, is_user=True)
            
            if not self.use_openai or not self.openai_client:
                logger.warning("[AVITO_BOT]OpenAI недоступен, используем fallback без functions")
                return self._get_fallback_response(message, ad_data, chat_id)
            
            response = self._get_openai_response_with_functions(
                message=message,
                ad_data=ad_data,
                chat_id=chat_id,
                use_functions=use_functions
            )
            
            # Добавить disclaimer если первое сообщение
            if self._is_first_message(chat_id):
                response = self.AI_DISCLAIMER + response
            
            if chat_id and response:
                self.add_to_dialogue_context(chat_id, response, is_user=False)
            
            return response
            
        except Exception as e:
            logger.error(f"[AVITO_BOT]Ошибка при обработке с functions: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self._get_fallback_response(message, ad_data, chat_id)
    
    def _get_openai_response_with_functions(
        self,
        message: str,
        ad_data: dict = None,
        chat_id: str = None,
        use_functions: bool = True
    ) -> str:
        """
        Генерация ответа OpenAI с поддержкой Function Calling
        
        SRP: Координирует процесс, делегирует задачи другим методам
        """
        logger.debug("Генерация OpenAI ответа с function calling")
        
        work_details = self.extract_work_details(message, ad_data)
        
        if work_details['city'] == "UNKNOWN_CITY":
            return self._handle_unknown_city(message, chat_id)
        
        messages = self._prepare_messages_for_openai(
            message=message,
            work_details=work_details,
            chat_id=chat_id,
            use_functions=use_functions
        )
        
        try:
            tools = get_function_definitions() if use_functions else None
            
            response = self.openai_client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto" if use_functions else None,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_TEMPERATURE,
                timeout=DEFAULT_TIMEOUT
            )
            
            assistant_message = response.choices[0].message
            
            if assistant_message.tool_calls:
                return self._handle_tool_calls(
                    messages=messages,
                    tool_calls=assistant_message.tool_calls,
                    assistant_content=assistant_message.content,
                    chat_id=chat_id,
                    ad_data=ad_data
                )
            else:
                logger.debug("AI не вызвал функции, обычный ответ")
                return assistant_message.content if assistant_message.content else self._get_fallback_response(message, ad_data, chat_id)
        
        except Exception as e:
            logger.error(f"Ошибка при вызове OpenAI с functions: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self._get_fallback_response(message, ad_data, chat_id)
    
    def _handle_unknown_city(self, message: str, chat_id: str = None) -> str:
        """
        Обработка случая когда город неизвестен
        """
        logger.debug("Город неизвестен, запрашиваем у клиента")
        system_prompt = self.prompt_builder.build_city_request_prompt()
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if chat_id:
            history = self.context_manager.get_openai_messages(chat_id, limit=5)
            messages.extend(history)
        
        messages.append({"role": "user", "content": message})
        
        response = self._call_openai_with_timeout(messages, max_tokens=100, temperature=0.3)
        
        return response if response else "Здравствуйте! Для расчета стоимости, пожалуйста, уточните ваш город."
    
    def _prepare_messages_for_openai(
        self,
        message: str,
        work_details: dict,
        chat_id: str = None,
        use_functions: bool = True
    ) -> list:
        """
        подготовка массива messages для OpenAI
        
        Returns:
            list: Массив сообщений [system, history..., user]
        """
        price_note = ""
        if work_details['hours'] and work_details['people']:
            price_calc = self.calculate_price(work_details)
            if price_calc:
                price_note = f"\n\nИНФО О РАСЧЕТЕ: {price_calc}"
        
        system_prompt = self.prompt_builder.build_system_prompt(
            work_details,
            dialogue_context="",
            include_pricing=True
        ) + price_note
        
        if use_functions:
            system_prompt += "\n\nВАЖНО: Когда клиент оставляет телефон, используй функцию create_bitrix_deal для создания заявки. После создания заявки подтверди клиенту что заявка принята и с ним свяжется менеджер. НЕ сообщай клиенту номер сделки."
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if chat_id:
            history = self.context_manager.get_openai_messages(chat_id, limit=10)
            messages.extend(history)
            logger.debug(f"Добавлена история: {len(history)} сообщений из БД")
        
        messages.append({"role": "user", "content": message})
        
        logger.debug(f"[AVITO_BOT] Подготовлено {len(messages)} сообщений для OpenAI")
        return messages
    
    def _handle_tool_calls(
        self,
        messages: list,
        tool_calls: list,
        assistant_content: str,
        chat_id: str = None,
        ad_data: dict = None
    ) -> str:
        """
        Обработка вызовов функций от AI
        
        Args:
            messages: Текущий массив сообщений
            tool_calls: Список вызовов функций от AI
            assistant_content: Контент ответа assistant
            chat_id: ID чата
            ad_data: Данные объявления
            
        Returns:
            str: Финальный ответ от AI после выполнения функций
        """
        
        logger.info(f"AI вызвал {len(tool_calls)} функций")
        
        messages.append({
            "role": "assistant",
            "content": assistant_content,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                }
                for tool_call in tool_calls
            ]
        })
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            logger.info(f"Выполнение функции: {function_name}")
            logger.debug(f"Аргументы: {json.dumps(function_args, ensure_ascii=False)}")
            
            context = {
                "chat_id": chat_id,
                "ad_data": ad_data
            }
            
            function_result = execute_function(function_name, function_args, context)
            result_formatted = format_function_result_for_ai(function_result)
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_formatted
            })
            
            logger.debug("Результат функции отправлен обратно в AI")
        
        return self._get_final_ai_response_after_functions(messages)
    
    def _get_final_ai_response_after_functions(self, messages: list) -> str:
        """
        SRP: Получение финального ответа от AI после выполнения функций
        
        Args:
            messages: Массив сообщений включая результаты функций
            
        Returns:
            str: Финальный ответ от AI
        """
        logger.debug("Запрос финального ответа от AI после выполнения функций")
        
        try:
            final_response = self.openai_client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_TEMPERATURE,
                timeout=DEFAULT_TIMEOUT
            )
            
            final_answer = final_response.choices[0].message.content
            logger.info("Финальный ответ получен от AI")
            return final_answer
            
        except Exception as e:
            logger.error(f"Ошибка при получении финального ответа: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return "Спасибо за информацию! Наш менеджер свяжется с вами в ближайшее время."
    
    def _get_fallback_response(self, message: str, ad_data: dict = None, chat_id: str = None) -> str:
        import re
        logger.debug("Использование fallback ответа")
        
        message_lower = message.lower()
        
        if re.search(r'(\+7|8)?[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}', message):
            logger.debug("Обнаружен телефон в fallback, пытаемся создать сделку")
            
            try:
                import utils
                phone = utils.telephone(message)
                if phone:
                    from .function_handlers import handle_create_bitrix_deal
                    
                    work_details = self.extract_work_details(message, ad_data)
                    context = {"chat_id": chat_id, "ad_data": ad_data}
                    
                    result = handle_create_bitrix_deal(
                        arguments={
                            "phone": phone,
                            "city": work_details.get('city', 'Не указан'),
                            "hours": work_details.get('hours'),
                            "people": work_details.get('people'),
                            "summary": "Fallback: OpenAI недоступен"
                        },
                        context=context
                    )
                    
                    if result.get("success"):
                        logger.info(f"Сделка создана через fallback: {result.get('deal_id')}")
                    else:
                        logger.error(f"Ошибка создания сделки в fallback: {result.get('error')}")
                        
            except Exception as e:
                logger.error(f"Критическая ошибка создания сделки в fallback: {e}")
            
            return "Спасибо! Номер принят, наш менеджер свяжется с вами в ближайшее время."
        
        if any(phrase in message_lower for phrase in ['1 человек', 'один грузчик', '1 грузчик', 'одного грузчика']):
            return "Здравствуйте! Минимально выезжают 2 грузчика. Для расчета стоимости оставьте номер телефона."
        
        if any(phrase in message_lower for phrase in ['офис', 'офисный', 'юр.лицо', 'оплата по счету', 'техзадание']):
            return "Здравствуйте! Юр.лицами занимается отдельный менеджер. Для быстрого расчета лучше оставить номер телефона, с вами свяжется менеджер."
        
        if any(phrase in message_lower for phrase in ['мусор', 'мусорка', 'контейнеры', 'вынести', 'спустить на мусорку', 'вывозите', 'вывоз']):
            return "Здравствуйте! Такой мусор нельзя выбрасывать на мусорку, так как за это могут оштрафовать. Нужно вывозить на место утилизации. Рассчитаю 2 грузчиков с минимальной ценой и автомобилем."
        
        if any(phrase in message_lower for phrase in ['холодильник', 'стиральная машина', 'спустить с этажа', 'сейф', 'банкомат', 'пианино']):
            return "Здравствуйте! Уточните вес предмета. Если вес более 100 кг, то нужен персональный расчет - оставьте номер телефона. Если менее 100 кг, то почасовая оплата из прайс-листа."
        
        if any(phrase in message_lower for phrase in ['за пределы города', 'снт', 'дачный поселок', 'км от города', 'за город']):
            return "Здравствуйте! Для выезда за пределы города нужен персональный расчет. Оставьте номер телефона для связи."
        
        work_details = self.extract_work_details(message, ad_data)
        
        if work_details['city'] != "UNKNOWN_CITY" and work_details['hours'] and work_details['people']:
            price_info = self.calculate_price(work_details)
            if price_info and price_info != "CITY_REQUEST":
                return price_info
        
        return "Здравствуйте! Для расчета стоимости услуг грузчиков отправьте, пожалуйста, номер телефона для связи."

