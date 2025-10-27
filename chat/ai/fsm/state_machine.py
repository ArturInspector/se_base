"""
Главный контроллер FSM (Finite State Machine)

SRP: Координация диалога через состояния
OCP: Легко расширяется новыми состояниями
DIP: Зависит от абстракций (TransitionEngine, MicroPromptBuilder)
"""
import logging
import time
import json
from typing import Optional, Dict, List, Tuple

from .states import DialogueState, StateContext
from .transitions import TransitionEngine
from .micro_prompts import MicroPromptBuilder
from .validators import AnswerValidator, get_metrics_collector

logger = logging.getLogger(__name__)


class DialogueStateMachine:
    """
    FSM Controller - управляет состояниями диалога
    
    Это "мозг" системы который:
    1. Определяет текущее состояние
    2. Извлекает данные из сообщения
    3. Решает куда переходить дальше
    4. Генерирует ответ для текущего состояния
    """
    
    def __init__(self, ai_processor):
        """
        Args:
            ai_processor: Экземпляр AvitoAIProcessor для извлечения данных и вызова AI
        """
        self.ai_processor = ai_processor
        self.transition_engine = TransitionEngine()
        self.prompt_builder = MicroPromptBuilder()
        self.validator = AnswerValidator()
        self.metrics = get_metrics_collector()
        
        # In-memory кэш контекстов
        # Ключ: chat_id, значение: StateContext
        self._contexts: Dict[str, StateContext] = {}
        
        logger.info("[FSM] DialogueStateMachine инициализирован с валидацией")
    
    def process_message(
        self,
        message: str,
        chat_id: str,
        user_id: int,
        ad_data: dict = None
    ) -> str:
        """
        Главный метод обработки сообщения через FSM
        
        Флоу:
        1. Получить текущее состояние (или создать новое)
        2. Извлечь данные из сообщения
        3. Определить следующее состояние
        4. Сгенерировать ответ для нового состояния
        5. Сохранить контекст
        
        Args:
            message: Сообщение от клиента
            chat_id: ID чата
            user_id: ID пользователя
            ad_data: Данные объявления (для извлечения города)
            
        Returns:
            str: Ответ для клиента
        """
        logger.info(f"[FSM] ═══ Обработка сообщения в чате {chat_id} ═══")
        logger.debug(f"[FSM] Сообщение: {message[:100]}...")
        
        try:
            # Шаг 1: Получаем контекст
            context = self._get_or_create_context(chat_id)
            logger.info(f"[FSM] Текущее состояние: {context.current_state}")
            
            # Шаг 2: Добавляем сообщение в историю
            self.ai_processor.add_to_dialogue_context(chat_id, message, is_user=True)
            
            # Шаг 3: Извлекаем данные из сообщения
            ai_extracted_data = self._extract_data_from_message(message, ad_data, context)
            if ai_extracted_data:
                logger.info(f"[FSM] ✅ Извлеченные данные: {ai_extracted_data}")
            else:
                logger.debug(f"[FSM] Данные не извлечены из сообщения")
            
            # Шаг 4: Определяем следующее состояние
            old_state = context.current_state
            next_state, transition_reason = self.transition_engine.determine_next_state(
                context=context,
                user_message=message,
                ai_extracted_data=ai_extracted_data
            )
            
            logger.info(f"[FSM] Переход: {old_state} → {next_state} ({transition_reason})")
            
            # Обновляем состояние
            context.current_state = next_state
            context.last_message_time = time.time()
            
            # Шаг 5: Генерируем ответ для нового состояния
            response, function_calls = self._generate_response_for_state(
                context=context,
                user_message=message,
                chat_id=chat_id
            )
            
            # Шаг 5.5: Валидация ответа (Grounding Policy)
            is_valid, issues = self.validator.validate_answer(response, context, function_calls)
            if not is_valid:
                logger.error(f"[FSM] ⚠️  ВАЛИДАЦИЯ НЕ ПРОШЛА!")
                for issue in issues:
                    logger.error(f"[FSM]     {issue}")
                self.metrics.record_validation_fail()
                self.metrics.record_hallucination()
                # В продакшене можно отправить в Telegram или регенерировать ответ
            
            # Шаг 6: Добавляем ответ в историю
            self.ai_processor.add_to_dialogue_context(chat_id, response, is_user=False)
            
            # Шаг 7: Сохраняем контекст
            self._save_context(context)
            
            logger.info(f"[FSM] ═══ Обработка завершена ═══")
            return response
            
        except Exception as e:
            logger.error(f"[FSM] Критическая ошибка обработки: {e}", exc_info=True)
            return self._get_emergency_fallback()
    
    def _get_or_create_context(self, chat_id: str) -> StateContext:
        """
        Получить или создать контекст для чата
        
        Порядок:
        1. Проверить in-memory кэш
        2. Попытаться загрузить из БД
        3. Создать новый
        """
        # Проверяем кэш
        if chat_id in self._contexts:
            logger.debug(f"[FSM] Контекст загружен из памяти")
            return self._contexts[chat_id]
        
        # Пытаемся загрузить из БД
        context = self._load_context_from_db(chat_id)
        if context:
            self._contexts[chat_id] = context
            logger.debug(f"[FSM] Контекст загружен из БД: {context.current_state}")
            return context
        
        # Создаем новый
        context = StateContext(
            current_state=DialogueState.GREETING,
            chat_id=chat_id
        )
        self._contexts[chat_id] = context
        logger.debug(f"[FSM] Создан новый контекст (GREETING)")
        return context
    
    def _extract_data_from_message(
        self,
        message: str,
        ad_data: dict,
        context: StateContext
    ) -> Dict:
        """
        Извлечь данные из сообщения используя AI extractors
        
        Returns:
            dict: {'city': 'Москва', 'hours': 3, 'people': 2, ...}
        """
        extracted = {}
        
        # Извлекаем город
        city = self.ai_processor.extract_city_from_message(message, ad_data)
        if city and city != "UNKNOWN_CITY":
            extracted['city'] = city
        
        # Извлекаем детали работы (часы, люди, тип)
        work_details = self.ai_processor.extract_work_details(message, ad_data)
        if work_details:
            if work_details.get('hours'):
                extracted['hours'] = work_details['hours']
            if work_details.get('people'):
                extracted['people'] = work_details['people']
            if work_details.get('work_type'):
                extracted['work_type'] = work_details['work_type']
        
        return extracted
    
    def _generate_response_for_state(
        self,
        context: StateContext,
        user_message: str,
        chat_id: str
    ) -> Tuple[str, List[str]]:
        """
        Генерация ответа для текущего состояния
        
        Использует:
        - Микро-промпт для состояния
        - Историю диалога (ограниченную)
        - Function calling для действий
        
        Returns:
            Tuple[str, List[str]]: (ответ, список_вызванных_функций)
        """
        state = context.current_state
        function_calls_made = []
        logger.debug(f"[FSM] Генерация ответа для {state}")
        
        # Строим микро-промпт для текущего состояния
        micro_prompt = self.prompt_builder.build_prompt(state, context)
        logger.debug(f"[FSM] Микро-промпт ({len(micro_prompt)} символов)")
        
        # Подготавливаем сообщения для OpenAI
        messages = [{"role": "system", "content": micro_prompt}]
        
        # Добавляем историю (ограниченную 5 последними сообщениями)
        history = self.ai_processor.context_manager.get_openai_messages(chat_id, limit=5)
        messages.extend(history)
        logger.debug(f"[FSM] История: {len(history)} сообщений")
        
        # Текущее сообщение
        messages.append({"role": "user", "content": user_message})
        
        # Вызываем OpenAI с функциями
        try:
            from ..functions import get_function_definitions
            from ..config import DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_TIMEOUT
            
            response = self.ai_processor.openai_client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                tools=get_function_definitions(),
                tool_choice="auto",
                max_tokens=300,  # Меньше чем в монолите - микро-промпты короче
                temperature=DEFAULT_TEMPERATURE,
                timeout=DEFAULT_TIMEOUT
            )
            
            assistant_message = response.choices[0].message
            
            # Если AI вызвал функции
            if assistant_message.tool_calls:
                logger.info(f"[FSM] AI вызвал {len(assistant_message.tool_calls)} функций")
                function_calls_made = [tc.function.name for tc in assistant_message.tool_calls]
                answer = self._handle_function_calls(
                    messages=messages,
                    tool_calls=assistant_message.tool_calls,
                    assistant_content=assistant_message.content,
                    context=context
                )
                return answer, function_calls_made
            
            # Обычный ответ
            answer = assistant_message.content or self._get_fallback_for_state(state, context)
            logger.debug(f"[FSM] Ответ: {answer[:100]}...")
            return answer, function_calls_made
            
        except Exception as e:
            logger.error(f"[FSM] Ошибка вызова OpenAI: {e}", exc_info=True)
            self.metrics.record_function_call_error()
            return self._get_fallback_for_state(state, context), []
    
    def _handle_function_calls(
        self,
        messages: list,
        tool_calls: list,
        assistant_content: str,
        context: StateContext
    ) -> str:
        """
        Обработка вызовов функций от AI
        
        Флоу:
        1. Добавить tool_calls в messages
        2. Выполнить каждую функцию
        3. Добавить результаты в messages
        4. Получить финальный ответ от AI
        """
        from ..function_handlers import execute_function, format_function_result_for_ai
        
        logger.info(f"[FSM] Обработка {len(tool_calls)} функций")
        
        # Добавляем сообщение assistant с tool_calls
        messages.append({
            "role": "assistant",
            "content": assistant_content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in tool_calls
            ]
        })
        
        # Выполняем каждую функцию
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            logger.info(f"[FSM] Выполнение: {function_name}({json.dumps(function_args, ensure_ascii=False)[:100]}...)")
            
            # Контекст для функции
            func_context = {
                "chat_id": context.chat_id,
                "ad_data": {}
            }
            
            # Выполняем
            result = execute_function(function_name, function_args, func_context)
            logger.debug(f"[FSM] Результат: {result}")
            
            # Обновляем контекст если это get_city_pricing
            if function_name == "get_city_pricing" and result.get("success"):
                context.ppr = result.get("ppr")
                context.min_hours = result.get("min_hours")
                logger.info(f"[FSM] Прайс обновлен: {context.ppr}₽/час, мин {context.min_hours}ч")
            
            # Форматируем результат для AI
            result_formatted = format_function_result_for_ai(result)
            
            # Добавляем в messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_formatted
            })
        
        # Получаем финальный ответ от AI
        return self._get_final_ai_response_after_functions(messages)
    
    def _get_final_ai_response_after_functions(self, messages: list) -> str:
        """
        Получить финальный ответ от AI после выполнения функций
        """
        logger.debug("[FSM] Запрос финального ответа после функций")
        
        try:
            from ..config import DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_TIMEOUT
            
            final_response = self.ai_processor.openai_client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                max_tokens=200,
                temperature=DEFAULT_TEMPERATURE,
                timeout=DEFAULT_TIMEOUT
            )
            
            final_answer = final_response.choices[0].message.content
            logger.info(f"[FSM] Финальный ответ: {final_answer[:100]}...")
            return final_answer
            
        except Exception as e:
            logger.error(f"[FSM] Ошибка финального ответа: {e}", exc_info=True)
            return "Спасибо! Наш менеджер свяжется с вами в ближайшее время."
    
    def _get_fallback_for_state(self, state: DialogueState, context: StateContext) -> str:
        """
        Fallback ответ если AI недоступен
        
        Простые, безопасные ответы для каждого состояния
        """
        fallbacks = {
            DialogueState.GREETING: "Здравствуйте! В каком городе вам нужны грузчики?",
            DialogueState.CITY_INQUIRY: "Уточните, пожалуйста, ваш город для расчета стоимости.",
            DialogueState.PRICE_INQUIRY: "Для точного расчета оставьте телефон, менеджер свяжется.",
            DialogueState.BOOKING_COLLECTION: "Для оформления заказа оставьте, пожалуйста, номер телефона.",
            DialogueState.BOOKING_CONFIRMATION: "Заявка принята! Наш менеджер свяжется с вами.",
            DialogueState.HANDOFF_OPERATOR: "Для персонального расчета оставьте телефон, менеджер перезвонит.",
            DialogueState.ISSUE_RESOLUTION: "Для решения вашего вопроса оставьте телефон, менеджер поможет.",
        }
        
        return fallbacks.get(state, "Оставьте телефон, наш менеджер свяжется с вами.")
    
    def _get_emergency_fallback(self) -> str:
        """Аварийный ответ при критической ошибке"""
        return "Извините, произошла техническая ошибка. Оставьте, пожалуйста, номер телефона — менеджер свяжется с вами."
    
    def _save_context(self, context: StateContext):
        """
        Сохранить контекст в БД
        
        TODO: Реализовать когда будет готова таблица dialogue_states
        """
        try:
            # Пока только логируем
            logger.debug(f"[FSM] Сохранение контекста: {context.current_state}, город={context.city}")
            
            # В будущем:
            # import chats_log
            # chats_log.api.save_dialogue_state(
            #     chat_id=context.chat_id,
            #     state_data=context.to_dict()
            # )
            
        except Exception as e:
            logger.error(f"[FSM] Ошибка сохранения контекста: {e}")
    
    def _load_context_from_db(self, chat_id: str) -> Optional[StateContext]:
        """
        Загрузить контекст из БД
        
        TODO: Реализовать когда будет готова таблица dialogue_states
        
        Returns:
            StateContext или None
        """
        try:
            # Пока всегда None (нет БД)
            return None
            
            # В будущем:
            # import chats_log
            # state_data = chats_log.api.load_dialogue_state(chat_id)
            # if state_data:
            #     return StateContext.from_dict(chat_id, state_data)
            # return None
            
        except Exception as e:
            logger.error(f"[FSM] Ошибка загрузки контекста: {e}")
            return None
    
    def get_context_info(self, chat_id: str) -> Dict:
        """
        Получить информацию о контексте (для debugging)
        
        Returns:
            dict: Текущее состояние и собранные данные
        """
        if chat_id not in self._contexts:
            return {"error": "Context not found"}
        
        ctx = self._contexts[chat_id]
        return {
            "state": ctx.current_state.value,
            "city": ctx.city,
            "hours": ctx.hours,
            "people": ctx.people,
            "phone": ctx.phone,
            "intent": ctx.intent,
            "is_legal": ctx.is_legal_entity,
            "retry_count": ctx.retry_count,
            "fallback_count": ctx.fallback_count
        }

