#!/usr/bin/env python3
"""
Консольный тестовый сервис для локального тестирования AI-бота
Демонстрирует работу с контекстом и историей диалога
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'se_base'))

import logging
from chat.ai.base import AvitoAIProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class ConsoleAITester:
    def __init__(self, use_functions: bool = True):
        logger.info("Инициализация тестового AI сервиса")
        self.processor = AvitoAIProcessor()
        self.processor.context_manager.use_db = False
        self.test_chat_id = "test_console_chat_001"
        self.test_user_id = 999999
        self.ad_data = self._prepare_test_ad_data()
        self.use_functions = use_functions
        logger.info(f"Function Calling: {'включен ✅' if use_functions else 'выключен ❌'}")
        
    def _prepare_test_ad_data(self) -> dict:
        """Подготовка тестовых данных объявления"""
        return {
            'url': 'https://www.avito.ru/moskva/predlozheniya_uslug/gruzchiki_test',
            'determined_city': 'Москва',
            'city_from_api': 'Москва',
            'item_id': 12345678
        }
    
    def print_separator(self, char="-", width=80):
        """Красивый разделитель"""
        print(char * width)
    
    def print_header(self, text: str):
        """Заголовок секции"""
        self.print_separator("=")
        print(f" {text}")
        self.print_separator("=")
    
    def display_context(self):
        """Показать текущий контекст диалога"""
        context = self.processor.context_manager.get_context(self.test_chat_id)
        
        if not context:
            print("📭 История диалога пуста")
            return
        
        print(f"\n📚 История диалога ({len(context)} сообщений):")
        self.print_separator()
        for idx, msg in enumerate(context, 1):
            role = "👤 Клиент" if msg['is_user'] else "🤖 Бот"
            print(f"{idx}. {role}: {msg['message'][:100]}...")
        self.print_separator()
    
    def process_user_message(self, message: str):
        """Обработка сообщения пользователя"""
        self.print_separator()
        print(f"👤 Клиент: {message}")
        
        try:
            if self.use_functions:
                response = self.processor.process_with_functions(
                    message=message,
                    user_id=self.test_user_id,
                    ad_data=self.ad_data,
                    chat_id=self.test_chat_id,
                    use_functions=True
                )
            else:
                response = self.processor.process_message(
                    message=message,
                    user_id=self.test_user_id,
                    ad_data=self.ad_data,
                    chat_id=self.test_chat_id
                )
            
            print(f"🤖 Бот: {response}")
            
        except Exception as e:
            logger.error(f"Ошибка обработки: {e}", exc_info=True)
            print(f"❌ Ошибка: {e}")
    
    def run_interactive(self):
        """Интерактивный режим"""
        func_status = "✅ ВКЛЮЧЕН" if self.use_functions else "❌ ВЫКЛЮЧЕН"
        self.print_header(f"🚀 ТЕСТОВЫЙ КОНСОЛЬНЫЙ AI-БОТ | Function Calling: {func_status}")
        print("""
Команды:
  - Введите сообщение для отправки боту
  - /history - показать историю диалога
  - /clear - очистить историю
  - /test - запустить тестовый сценарий
  - /testfunc - тест с function calling (создание сделки)
  - /toggle - переключить function calling
  - /exit или /quit - выход
        """)
        self.print_separator()
        
        while True:
            try:
                user_input = input("\n>>> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['/exit', '/quit', 'exit', 'quit']:
                    print("👋 До свидания!")
                    break
                
                if user_input.lower() == '/history':
                    self.display_context()
                    continue
                
                if user_input.lower() == '/clear':
                    self.processor.context_manager.clear_old_contexts()
                    print("✅ История диалога очищена")
                    continue
                
                if user_input.lower() == '/test':
                    self.run_test_scenario()
                    continue
                
                if user_input.lower() == '/testfunc':
                    self.run_function_test()
                    continue
                
                if user_input.lower() == '/toggle':
                    self.use_functions = not self.use_functions
                    status = "✅ включен" if self.use_functions else "❌ выключен"
                    print(f"Function Calling теперь {status}")
                    continue
                
                self.process_user_message(user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 Прервано пользователем")
                break
            except Exception as e:
                logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
    
    def run_test_scenario(self):
        """Запуск тестового сценария"""
        self.print_header("🧪 ТЕСТОВЫЙ СЦЕНАРИЙ")
        
        print("Введите сообщения для тестирования диалога")
        print("Для завершения введите пустую строку или /stop\n")
        
        step = 1
        while True:
            try:
                message = input(f"[Шаг {step}] >>> ").strip()
                
                if not message or message.lower() in ['/stop', '/exit']:
                    break
                
                self.process_user_message(message)
                step += 1
                print()
                
            except KeyboardInterrupt:
                print("\n❌ Тест прерван")
                break
        
        print("\n")
        self.display_context()
        self.print_header("✅ ТЕСТОВЫЙ СЦЕНАРИЙ ЗАВЕРШЕН")
    
    def run_function_test(self):
        """Тест Function Calling - создание сделки в Битриксе"""
        self.print_header("🔧 ТЕСТ FUNCTION CALLING")
        
        print("""
Этот тест проверяет работу OpenAI Function Calling.
AI должен автоматически вызвать функцию create_bitrix_deal
когда получит телефон от клиента.
        """)
        self.print_separator()
        
        test_messages = [
            "Здравствуйте, нужно 2 грузчика в Москве на 4 часа",
            "Мой телефон +7 999 888 77 66"
        ]
        
        print("\n[Шаг 1/2] Клиент описывает задачу")
        self.process_user_message(test_messages[0])
        input("\nНажмите Enter для продолжения...")
        
        print("\n[Шаг 2/2] Клиент оставляет телефон")
        print("⚠️  Ожидаем что AI вызовет функцию create_bitrix_deal")
        self.process_user_message(test_messages[1])
        
        print("\n")
        self.print_separator()
        print("\n✅ Если вы видели логи 'Выполнение функции: create_bitrix_deal' - тест прошел!")
        print("✅ Сделка должна быть создана в Битрикс24")
        self.print_header("ТЕСТ ЗАВЕРШЕН")
    
    def run_single_test(self, message: str):
        """Одиночный тест сообщения"""
        self.print_header(f"ТЕСТ: {message}")
        self.process_user_message(message)
        self.print_separator()


def main():
    if len(sys.argv) > 1:
        tester = ConsoleAITester()
        message = " ".join(sys.argv[1:])
        tester.run_single_test(message)
    else:
        tester = ConsoleAITester()
        tester.run_interactive()


if __name__ == "__main__":
    main()

