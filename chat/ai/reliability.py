"""
Reliability Patterns для Production

Реализует паттерны:
1. Retry с exponential backoff
2. Circuit Breaker
3. Timeout management
4. Metrics collection
"""
import time
import logging
from typing import Callable, Any, Optional
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class RetryConfig:
    """Конфигурация retry логики"""
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


def retry_with_backoff(
    config: RetryConfig = None,
    exceptions: tuple = (Exception,),
    on_retry: Callable = None
):
    """
    Декоратор для retry с exponential backoff
    
    Usage:
        @retry_with_backoff(
            config=RetryConfig(max_attempts=3),
            exceptions=(ConnectionError, TimeoutError)
        )
        def unstable_api_call():
            ...
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            delay = config.initial_delay
            
            while attempt <= config.max_attempts:
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    if attempt == config.max_attempts:
                        logger.error(
                            f"[RETRY] {func.__name__} failed after {config.max_attempts} attempts: {e}"
                        )
                        raise
                    
                    if config.jitter:
                        import random
                        actual_delay = delay * (0.5 + random.random())
                    else:
                        actual_delay = delay
                    
                    logger.warning(
                        f"[RETRY] {func.__name__} attempt {attempt}/{config.max_attempts} "
                        f"failed: {e}. Retrying in {actual_delay:.2f}s..."
                    )
                    
                    if on_retry:
                        on_retry(attempt, e)
                    
                    time.sleep(actual_delay)
                    
                    attempt += 1
                    delay = min(delay * config.exponential_base, config.max_delay)
            
            return None
        
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit Breaker Pattern
    
    Предотвращает повторные вызовы упавшего сервиса.
    
    States:
        CLOSED - нормальная работа
        OPEN - сервис упал, блокируем вызовы
        HALF_OPEN - пробуем восстановить
    """
    
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = self.CLOSED
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Вызов функции через circuit breaker"""
        
        with self._lock:
            if self.state == self.OPEN:
                if self._should_attempt_reset():
                    logger.info(f"[CIRCUIT] {func.__name__}: Переход в HALF_OPEN")
                    self.state = self.HALF_OPEN
                else:
                    logger.warning(f"[CIRCUIT] {func.__name__}: OPEN, блокируем вызов")
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker OPEN для {func.__name__}"
                    )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Проверка что прошло достаточно времени для попытки восстановления"""
        if self.last_failure_time is None:
            return True
        return (datetime.now() - self.last_failure_time).seconds >= self.recovery_timeout
    
    def _on_success(self):
        """Обработка успешного вызова"""
        with self._lock:
            self.failure_count = 0
            
            if self.state == self.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    logger.info("[CIRCUIT] Восстановление: переход в CLOSED")
                    self.state = self.CLOSED
                    self.success_count = 0
    
    def _on_failure(self):
        """Обработка неудачного вызова"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            self.success_count = 0
            
            if self.failure_count >= self.failure_threshold:
                logger.error(
                    f"[CIRCUIT] Достигнут порог ошибок ({self.failure_count}), "
                    f"переход в OPEN"
                )
                self.state = self.OPEN
    
    def reset(self):
        """Принудительный сброс circuit breaker"""
        with self._lock:
            logger.info("[CIRCUIT] Принудительный reset")
            self.state = self.CLOSED
            self.failure_count = 0
            self.success_count = 0


class CircuitBreakerOpenError(Exception):
    """Исключение когда circuit breaker в состоянии OPEN"""
    pass


class FunctionCallMetrics:
    """
    Метрики вызовов функций для мониторинга
    
    Отслеживает:
    - Количество вызовов
    - Success rate
    - Latency (среднее, p95, p99)
    - Errors
    """
    
    def __init__(self):
        self.calls = defaultdict(int)
        self.successes = defaultdict(int)
        self.failures = defaultdict(int)
        self.errors = defaultdict(list)
        self.latencies = defaultdict(list)
        self._lock = threading.Lock()
    
    def record_call(
        self,
        function_name: str,
        success: bool,
        latency_ms: float,
        error: Optional[str] = None
    ):
        """записать результат вызова функции"""
        with self._lock:
            self.calls[function_name] += 1
            
            if success:
                self.successes[function_name] += 1
            else:
                self.failures[function_name] += 1
                if error:
                    self.errors[function_name].append({
                        'timestamp': datetime.now(),
                        'error': error
                    })
            
            self.latencies[function_name].append(latency_ms)
            
            # ограничиваем размер истории (последние 1000)
            if len(self.latencies[function_name]) > 1000:
                self.latencies[function_name] = self.latencies[function_name][-1000:]
            if len(self.errors[function_name]) > 100:
                self.errors[function_name] = self.errors[function_name][-100:]
    
    def get_success_rate(self, function_name: str) -> float:
        """Получить success rate для функции"""
        total = self.calls[function_name]
        if total == 0:
            return 0.0
        return (self.successes[function_name] / total) * 100
    
    def get_avg_latency(self, function_name: str) -> float:
        """Получить среднюю latency"""
        latencies = self.latencies[function_name]
        if not latencies:
            return 0.0
        return sum(latencies) / len(latencies)
    
    def get_percentile_latency(self, function_name: str, percentile: int = 95) -> float:
        """Получить percentile latency (p95, p99)"""
        latencies = sorted(self.latencies[function_name])
        if not latencies:
            return 0.0
        
        index = int(len(latencies) * (percentile / 100.0))
        return latencies[min(index, len(latencies) - 1)]
    
    def get_recent_errors(self, function_name: str, limit: int = 10) -> list:
        """Получить последние ошибки"""
        return self.errors[function_name][-limit:]
    
    def get_report(self) -> dict:
        """Получить полный отчет по всем функциям"""
        report = {}
        
        for func_name in self.calls.keys():
            report[func_name] = {
                'total_calls': self.calls[func_name],
                'successes': self.successes[func_name],
                'failures': self.failures[func_name],
                'success_rate': f"{self.get_success_rate(func_name):.2f}%",
                'avg_latency_ms': f"{self.get_avg_latency(func_name):.2f}",
                'p95_latency_ms': f"{self.get_percentile_latency(func_name, 95):.2f}",
                'p99_latency_ms': f"{self.get_percentile_latency(func_name, 99):.2f}",
                'recent_errors': len(self.get_recent_errors(func_name))
            }
        
        return report
    


_metrics = FunctionCallMetrics()
_circuit_breakers = {}


def get_metrics() -> FunctionCallMetrics:
    """Получить глобальный инстанс метрик"""
    return _metrics


def get_circuit_breaker(name: str) -> CircuitBreaker:
    """Получить circuit breaker по имени"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker()
    return _circuit_breakers[name]


def monitored_function(function_name: str = None):
    """
    Декоратор для мониторинга функций
    
    Автоматически записывает метрики вызовов
    """
    def decorator(func):
        name = function_name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            error = None
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
                
            except Exception as e:
                error = str(e)
                raise
                
            finally:
                latency_ms = (time.time() - start_time) * 1000
                _metrics.record_call(name, success, latency_ms, error)
        
        return wrapper
    return decorator
