import signal
import threading
from typing import Optional
import logging
import openai

import config

from .extractors import CityExtractor, WorkDetailsExtractor
from .pricing import PricingCalculator
from .prompts import PromptBuilder
from .context import DialogueContextManager
from .config import DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[AVITO_BOT] %(levelname)s: %(funcName)s: %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class AvitoAIProcessor:
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
        
        logger.debug(f"Подготовка ad_data для item_id={item_id}, chat_id={chat_id}")
        
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
        
        ad_city = self.city_extractor.extract_city_from_message('тест', ad_data)
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
        logger.info(f"Обработка сообщения: '{message[:50]}...'")
        
        try:
            if chat_id:
                self.add_to_dialogue_context(chat_id, message, is_user=True)
            
            response = None
            if self.use_openai and self.openai_client:
                logger.debug("Используем OpenAI для обработки")
                try:
                    response = self._get_openai_response(message, ad_data, chat_id)
                except Exception as e:
                    logger.error(f"Ошибка OpenAI: {e}")
                    response = self._get_fallback_response(message, ad_data)
            else:
                logger.debug("OpenAI недоступен, используем fallback")
                response = self._get_fallback_response(message, ad_data)
            
            if chat_id and response:
                self.add_to_dialogue_context(chat_id, response, is_user=False)
            
            return response
                
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            return self._get_fallback_response(message, ad_data)
    
    def _get_openai_response(self, message: str, ad_data: dict = None, chat_id: str = None) -> str:
        logger.debug("Генерация OpenAI ответа")
        
        work_details = self.extract_work_details(message, ad_data)
        logger.debug(f"Извлечены детали: {work_details}")
        
        if work_details['city'] == "UNKNOWN_CITY":
            logger.debug("Город неизвестен, запрашиваем у клиента")
            system_prompt = self.prompt_builder.build_city_request_prompt()
            
            messages = [{"role": "system", "content": system_prompt}]
            
            if chat_id:
                history = self.context_manager.get_openai_messages(chat_id, limit=5)
                messages.extend(history)
            
            messages.append({"role": "user", "content": message})
            
            response = self._call_openai_with_timeout(messages, max_tokens=100, temperature=0.3)
            
            if response:
                return response
            return "Здравствуйте! Для расчета стоимости, пожалуйста, уточните ваш город."
        
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
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if chat_id:
            history = self.context_manager.get_openai_messages(chat_id, limit=10)
            messages.extend(history)
            logger.debug(f"Добавлена история: {len(history)} сообщений из БД")
        
        messages.append({"role": "user", "content": message})
        
        logger.debug(f"Отправка в OpenAI: {len(messages)} сообщений (system + история + текущее)")
        
        response = self._call_openai_with_timeout(messages, max_tokens=400, temperature=0.7)
        
        if response:
            logger.debug("OpenAI ответ получен")
            return response
        
        return self._get_fallback_response(message, ad_data)
    
    def _get_fallback_response(self, message: str, ad_data: dict = None) -> str:
        import re
        logger.debug("Использование fallback ответа")
        
        message_lower = message.lower()
        
        if re.search(r'(\+7|8)?[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}', message):
            logger.debug("Обнаружен телефон в сообщении")
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

