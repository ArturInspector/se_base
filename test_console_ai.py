#!/usr/bin/env python3
"""
Консольный тестовый сервис для локального тестирования AI-бота
Демонстрирует работу с контекстом и историей диалога
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'se_base'))

import logging
from chat.ai import AvitoAIProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class ConsoleAITester:
    def __init__(self):
        logger.info("Инициализация тестового AI сервиса")
        self.processor = AvitoAIProcessor()
        self.processor.context_manager.use_db = False
        self.test_chat_id = "test_console_chat_001"
        self.test_user_id = 999999
        self.ad_data = self._prepare_test_ad_data()
        
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
        self.print_header("🚀 ТЕСТОВЫЙ КОНСОЛЬНЫЙ AI-БОТ")
        print("""
Команды:
  - Введите сообщение для отправки боту
  - /history - показать историю диалога
  - /clear - очистить историю
  - /test - запустить тестовый сценарий
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
                
                self.process_user_message(user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 Прервано пользователем")
                break
            except Exception as e:
                logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
    
    def run_test_scenario(self):
        """Запуск тестового сценария"""
        self.print_header("🧪 ТЕСТОВЫЙ СЦЕНАРИЙ")
        
        test_messages = [
            "Здравствуйте, сколько стоит грузчик?",
            "Мне нужно на 3 часа",
            "2 человека достаточно?",
            "А можно номер телефона оставить для связи",
            "+7 999 123 45 67"
        ]
        
        print("Запускаем диалог с 5 сообщениями...\n")
        
        for idx, message in enumerate(test_messages, 1):
            print(f"\n[Шаг {idx}/5]")
            self.process_user_message(message)
            input("\nНажмите Enter для продолжения...")
        
        print("\n")
        self.display_context()
        self.print_header("✅ ТЕСТОВЫЙ СЦЕНАРИЙ ЗАВЕРШЕН")
    
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

