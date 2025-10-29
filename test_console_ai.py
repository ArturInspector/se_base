#!/usr/bin/env python3
"""
Консольный тестовый сервис для локального тестирования AI-бота
Демонстрирует работу с контекстом и историей диалога
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'se_base'))

import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from chat.ai.simple_processor import SimpleAIProcessor
from chat.models import AvitoMessageModel, AvitoMessagePayload, AvitoMessageValue, AvitoMessageContent
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class ScenarioParser:
    """Парсер тестовых сценариев из текстовых файлов"""
    
    @staticmethod
    def extract_city_from_scenario_name(name: str) -> str:
        """Извлечь город из названия сценария"""
        import re
        
        # Паттерны для поиска городов
        city_patterns = [
            r'\((.*?)\)',  # В скобках: (Ростов-на-Дону)
            r'г\.?\s+([А-Яа-яёЁ\-]+)',  # г. Москва
            r'город\s+([А-Яа-яёЁ\-]+)',  # город Казань
        ]
        
        for pattern in city_patterns:
            match = re.search(pattern, name)
            if match:
                city = match.group(1).strip()
                # Убираем лишние слова
                city = re.sub(r'обл\.|область|край|респ\.|республика', '', city).strip()
                city = city.split(',')[0].strip()  # Берем первое до запятой
                if city and len(city) > 2:
                    return city
        
        return None
    
    @staticmethod
    def parse_file(file_path: str) -> List[Dict]:
        """
        Парсит файл со сценариями
        
        Формат:
            # Название теста
            USER: сообщение
            BOT: ожидаемый ответ (опционально, для валидации)
            USER: следующее
            ---
            # Следующий тест
        """
        scenarios = []
        current_scenario = None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip()
                
                # Пустые строки пропускаем
                if not line:
                    continue
                
                # Разделитель сценариев
                if line.strip() == '---':
                    if current_scenario and current_scenario['messages']:
                        scenarios.append(current_scenario)
                    current_scenario = None
                    continue
                
                # Название теста (комментарий)
                if line.startswith('#'):
                    if current_scenario and current_scenario['messages']:
                        scenarios.append(current_scenario)
                    scenario_name = line[1:].strip()
                    current_scenario = {
                        'name': scenario_name,
                        'city': ScenarioParser.extract_city_from_scenario_name(scenario_name),
                        'messages': []
                    }
                    continue
                
                # Сообщение пользователя
                if line.startswith('USER:') or line.startswith('Клиент:'):
                    if not current_scenario:
                        current_scenario = {'name': 'Unnamed', 'messages': []}
                    
                    text = line.split(':', 1)[1].strip()
                    if text:  # Игнорируем пустые
                        current_scenario['messages'].append({
                            'role': 'user',
                            'text': text
                        })
                
                # Ожидаемый ответ бота (для валидации)
                elif line.startswith('BOT:') or line.startswith('Бот:'):
                    if not current_scenario:
                        continue
                    
                    text = line.split(':', 1)[1].strip()
                    if text:
                        current_scenario['messages'].append({
                            'role': 'bot',
                            'expected': text
                        })
        
        # Добавляем последний сценарий
        if current_scenario and current_scenario['messages']:
            scenarios.append(current_scenario)
        
        return scenarios


class DialogueLogger:
    """Логирование диалогов в файлы для анализа конверсии"""
    
    def __init__(self, log_dir: str = "test_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_session_file = None
        self.start_new_session()
    
    def start_new_session(self):
        """Начать новую сессию логирования"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session_file = self.log_dir / f"session_{timestamp}.txt"
        
        with open(self.current_session_file, 'w', encoding='utf-8') as f:
            f.write(f"=== ТЕСТОВАЯ СЕССИЯ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
    
    def log_message(self, role: str, message: str, metadata: dict = None):
        """Записать сообщение в лог"""
        if not self.current_session_file:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        with open(self.current_session_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {role}:\n")
            f.write(f"{message}\n")
            
            if metadata:
                f.write(f"Метаданные: {metadata}\n")
            
            f.write("\n" + "-" * 80 + "\n\n")
    
    def log_scenario_start(self, scenario_name: str):
        """Начало нового сценария"""
        if not self.current_session_file:
            return
        
        with open(self.current_session_file, 'a', encoding='utf-8') as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"СЦЕНАРИЙ: {scenario_name}\n")
            f.write("=" * 80 + "\n\n")
    
    def log_scenario_end(self, results: dict = None):
        """Завершение сценария"""
        if not self.current_session_file:
            return
        
        with open(self.current_session_file, 'a', encoding='utf-8') as f:
            f.write("\n" + "~" * 80 + "\n")
            if results:
                f.write(f"РЕЗУЛЬТАТ: {results}\n")
            f.write("~" * 80 + "\n\n")


class ConsoleAITester:
    def __init__(self):
        logger.info("Инициализация тестового AI сервиса (Simple Processor)")
        self.processor = SimpleAIProcessor()
        self.test_chat_id = "test_console_chat_001"
        self.test_user_id = 999999
        self.ad_data = self._prepare_test_ad_data(None)  # По умолчанию без города
        
        # ✅ Контекст пустой при запуске → disclaimer будет показан автоматически
        logger.info(f"✅ SimpleAIProcessor initialized for chat_id: {self.test_chat_id}")
        
        # Логирование диалогов
        self.dialogue_logger = DialogueLogger()
        logger.info(f"📝 Логи сохраняются в: {self.dialogue_logger.current_session_file}")
        logger.info("✅ Новая архитектура: AI-over-AI with Context Analyzer")
        
    def _prepare_test_ad_data(self, city: str = None) -> dict:
        """
        Подготовка тестовых данных объявления
        
        Args:
            city: Город для объявления. Если None - бот сам определит из диалога
        """
        if city:
            return {
                'url': f'https://www.avito.ru/{city}/predlozheniya_uslug/gruzchiki_test',
                'determined_city': city,
                'city_from_api': city,
                'item_id': 12345678
            }
        else:
            # Без города - бот сам должен спросить/определить
            return {
                'url': 'https://www.avito.ru/predlozheniya_uslug/gruzchiki_test',
                'item_id': 12345678
            }
    
    def _create_mock_avito_message(self, message: str) -> AvitoMessageModel:
        """
        Создание mock AvitoMessageModel для логирования
        
        Args:
            message: Текст сообщения
        
        Returns:
            Mock AvitoMessageModel для chats_log
        """
        message_id = f"test_msg_{int(time.time() * 1000)}"
        
        return AvitoMessageModel(
            id=message_id,
            version="1.0",
            timestamp=int(time.time()),
            payload=AvitoMessagePayload(
                type='message',
                value=AvitoMessageValue(
                    id=message_id,
                    chat_id=self.test_chat_id,
                    user_id=self.test_user_id,
                    author_id=self.test_user_id,
                    created=int(time.time()),
                    type='text',
                    chat_type='u2i',
                    item_id=self.ad_data.get('item_id'),
                    content=AvitoMessageContent(text=message)
                )
            )
        )
    
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
            role = "👤 Клиент" if msg.get('is_user') else "🤖 Бот"
            message_text = msg.get('message', '')
            print(f"{idx}. {role}: {message_text[:100]}...")
        self.print_separator()
    
    def process_user_message(self, message: str):
        """Обработка сообщения пользователя"""
        self.print_separator()
        print(f"👤 Клиент: {message}")
        
        # Логируем сообщение клиента
        self.dialogue_logger.log_message("КЛИЕНТ", message)
        
        try:
            # Создаем mock AvitoMessageModel для логирования
            mock_model = self._create_mock_avito_message(message)
            
            # Вызываем новый процессор
            response, metadata = self.processor.process(
                message=message,
                chat_id=self.test_chat_id,
                ad_data=self.ad_data,
                avito_message_model=mock_model,
                return_metadata=True
            )
            
            # Показываем метаданные
            if metadata:
                if metadata.get('customer_type'):
                    confidence = metadata.get('customer_type_confidence', 0)
                    print(f"\n 📊 Тип клиента: {metadata['customer_type']} (confidence: {confidence:.2f})")
                if metadata.get('action'):
                    print(f"   └─ Действие: {metadata['action']}")
                if metadata.get('template_id'):
                    print(f"   └─ Шаблон: {metadata['template_id']}")
            
            print(f"\n🤖 Бот: {response}")
            
            # Логируем ответ бота
            self.dialogue_logger.log_message("БОТ", response, metadata)
            
        except Exception as e:
            logger.error(f"Ошибка обработки: {e}", exc_info=True)
            error_msg = f"❌ Ошибка: {e}"
            print(error_msg)
            self.dialogue_logger.log_message("ОШИБКА", str(e))
    
    def run_interactive(self):
        """Интерактивный режим"""
        self.print_header("🚀 ТЕСТОВЫЙ КОНСОЛЬНЫЙ AI-БОТ | Simple Processor")
        print("""
📋 Новая архитектура:
  ✅ One AI Call → Structured JSON
  ✅ Business Rules → Deterministic Logic
  ✅ Templates → No Hallucinations

Команды:
  - Введите сообщение для отправки боту
  - /history - показать историю диалога
  - /clear - очистить историю
  - /test - запустить тестовый сценарий
  - /run <файл> - запустить сценарии из файла
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
                
                if user_input.lower().startswith('/run'):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        print("❌ Укажите файл: /run <путь_к_файлу>")
                        print("   Пример: /run test_scenarios/example_scenario.txt")
                        print("   Или просто: /run example_scenario.txt")
                    else:
                        self.run_scenarios_from_file(parts[1])
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
    
    def run_single_test(self, message: str):
        """Одиночный тест сообщения"""
        self.print_header(f"ТЕСТ: {message}")
        self.process_user_message(message)
        self.print_separator()
    
    def run_scenarios_from_file(self, file_path: str):
        """Запуск сценариев из файла"""
        try:
            # Пробуем найти файл
            if not os.path.exists(file_path):
                # Проверяем в test_scenarios/
                alt_path = os.path.join(os.path.dirname(__file__), '..', 'test_scenarios', file_path)
                if os.path.exists(alt_path):
                    file_path = alt_path
                else:
                    print(f"❌ Файл не найден: {file_path}")
                    return
            
            scenarios = ScenarioParser.parse_file(file_path)
            
            if not scenarios:
                print(f"❌ Не найдено сценариев в файле {file_path}")
                return
            
            self.print_header(f"📋 ЗАПУСК СЦЕНАРИЕВ ИЗ ФАЙЛА: {file_path}")
            print(f"Найдено сценариев: {len(scenarios)}\n")
            
            scenario_results = []
            
            for idx, scenario in enumerate(scenarios, 1):
                self.print_separator("=")
                print(f"🧪 СЦЕНАРИЙ #{idx}: {scenario['name']}")
                if scenario.get('city'):
                    print(f"   📍 Город из теста: {scenario['city']}")
                self.print_separator("=")
                
                # Логируем начало сценария
                self.dialogue_logger.log_scenario_start(f"#{idx}: {scenario['name']}")
                
                # Обновляем ad_data с городом из сценария (если есть)
                self.ad_data = self._prepare_test_ad_data(scenario.get('city'))
                
                # Очищаем контекст перед каждым сценарием
                self.processor.context_manager.clear_old_contexts()
                
                # Выполняем сообщения
                scenario_start_time = datetime.now()
                for msg_idx, message in enumerate(scenario['messages'], 1):
                    if message['role'] == 'user':
                        print(f"\n[{msg_idx}] ", end="")
                        self.process_user_message(message['text'])
                    elif message['role'] == 'bot':
                        # TODO: можно добавить валидацию ожидаемого ответа
                        pass
                
                scenario_duration = (datetime.now() - scenario_start_time).total_seconds()
                
                # Собираем результаты сценария
                result = {
                    'name': scenario['name'],
                    'duration': f"{scenario_duration:.2f}s",
                    'messages_count': len([m for m in scenario['messages'] if m['role'] == 'user'])
                }
                
                scenario_results.append(result)
                
                # Логируем завершение сценария
                self.dialogue_logger.log_scenario_end(result)
                
                print("\n")
                if idx < len(scenarios):
                    response = input("Нажмите Enter для следующего сценария (или 'q' для выхода): ")
                    if response.lower() == 'q':
                        break
                    print()
            
            # Итоговый отчет
            self.print_header("✅ ВСЕ СЦЕНАРИИ ВЫПОЛНЕНЫ")
            print("\n📊 СТАТИСТИКА:\n")
            for idx, result in enumerate(scenario_results, 1):
                print(f"{idx}. {result['name']}")
                print(f"   Длительность: {result['duration']}")
                print(f"   Сообщений: {result['messages_count']}")
                print()
            
            print(f"\n📝 Полный лог сохранен в: {self.dialogue_logger.current_session_file}")
            
        except Exception as e:
            logger.error(f"Ошибка выполнения сценариев: {e}", exc_info=True)
            print(f"❌ Ошибка: {e}")


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

