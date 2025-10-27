"""
Валидация ответов AI и сбор метрик качества

SRP: Только валидация и метрики
"""
import logging
from typing import Tuple, List, Dict
from .states import DialogueState, StateContext

logger = logging.getLogger(__name__)


class AnswerValidator:
    """Валидатор ответов AI для предотвращения галлюцинаций"""
    
    def validate_answer(
        self, 
        response: str, 
        context: StateContext,
        function_calls: List = None
    ) -> Tuple[bool, List[str]]:
        """
        Проверка ответа AI на корректность
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, список проблем)
        """
        issues = []
        
        # Проверка 1: Ответ не пустой
        if not response or len(response.strip()) < 5:
            issues.append("Пустой или слишком короткий ответ")
        
        # Проверка 2: Нет галлюцинаций по данным
        if context.city and context.city not in response and context.current_state != DialogueState.BOOKING_CONFIRMATION:
            # В состоянии подтверждения необязательно упоминать город
            pass
        
        # Проверка 3: Не просит данные, которые уже есть
        if context.people and "сколько грузчиков" in response.lower():
            issues.append(f"Повторно запрашивает количество грузчиков (уже есть: {context.people})")
        
        if context.hours and "сколько часов" in response.lower():
            issues.append(f"Повторно запрашивает часы (уже есть: {context.hours})")
        
        if context.city and "какой город" in response.lower():
            issues.append(f"Повторно запрашивает город (уже есть: {context.city})")
        
        # Проверка 4: Некорректные переходы состояний
        if context.current_state == DialogueState.COMPLETED and "телефон" in response.lower():
            issues.append("Запрашивает телефон после закрытия сделки")
        
        is_valid = len(issues) == 0
        
        if not is_valid:
            logger.warning(f"[VALIDATOR] Проблемы в ответе: {', '.join(issues)}")
        
        return is_valid, issues


class MetricsCollector:
    """Сбор метрик качества диалогов для мониторинга"""
    
    def __init__(self):
        self.metrics = {
            'total_messages': 0,
            'validation_fails': 0,
            'hallucinations': 0,
            'function_call_errors': 0,
            'successful_deals': 0,
            'avg_messages_to_phone': [],
            'state_transitions': {}
        }
    
    def record_message(self):
        """Записать обработанное сообщение"""
        self.metrics['total_messages'] += 1
    
    def record_validation_fail(self):
        """Записать провал валидации"""
        self.metrics['validation_fails'] += 1
    
    def record_hallucination(self):
        """Записать галлюцинацию AI"""
        self.metrics['hallucinations'] += 1
    
    def record_function_call_error(self):
        """Записать ошибку вызова функции"""
        self.metrics['function_call_errors'] += 1
    
    def record_successful_deal(self, messages_count: int):
        """Записать успешную сделку"""
        self.metrics['successful_deals'] += 1
        self.metrics['avg_messages_to_phone'].append(messages_count)
    
    def record_state_transition(self, from_state: DialogueState, to_state: DialogueState):
        """Записать переход состояния"""
        key = f"{from_state.name} -> {to_state.name}"
        self.metrics['state_transitions'][key] = self.metrics['state_transitions'].get(key, 0) + 1
    
    def get_stats(self) -> Dict:
        """Получить статистику"""
        stats = self.metrics.copy()
        
        if stats['avg_messages_to_phone']:
            stats['avg_messages_to_phone_value'] = sum(stats['avg_messages_to_phone']) / len(stats['avg_messages_to_phone'])
        else:
            stats['avg_messages_to_phone_value'] = 0
        
        if stats['total_messages'] > 0:
            stats['validation_fail_rate'] = stats['validation_fails'] / stats['total_messages'] * 100
            stats['hallucination_rate'] = stats['hallucinations'] / stats['total_messages'] * 100
        else:
            stats['validation_fail_rate'] = 0
            stats['hallucination_rate'] = 0
        
        return stats
    
    def print_report(self):
        """Вывести отчет в консоль"""
        stats = self.get_stats()
        
        print("\n" + "="*80)
        print(" 📊 ОТЧЕТ ПО КАЧЕСТВУ ДИАЛОГОВ")
        print("="*80)
        print(f"Всего сообщений: {stats['total_messages']}")
        print(f"Успешных сделок: {stats['successful_deals']}")
        
        if stats['successful_deals'] > 0:
            print(f"Среднее сообщений до телефона: {stats['avg_messages_to_phone_value']:.1f}")
        
        print(f"\n⚠️  ПРОБЛЕМЫ:")
        print(f"  Провалов валидации: {stats['validation_fails']} ({stats['validation_fail_rate']:.1f}%)")
        print(f"  Галлюцинаций: {stats['hallucinations']} ({stats['hallucination_rate']:.1f}%)")
        print(f"  Ошибок function calling: {stats['function_call_errors']}")
        
        if stats['state_transitions']:
            print(f"\n🔄 ПЕРЕХОДЫ СОСТОЯНИЙ:")
            for transition, count in sorted(stats['state_transitions'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {transition}: {count}")
        
        print("="*80 + "\n")
    
    def reset(self):
        """Сбросить метрики"""
        self.__init__()


# Singleton для метрик
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """Получить глобальный экземпляр MetricsCollector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

