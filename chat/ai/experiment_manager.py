"""
A/B Testing Experiment Manager

SUPER SIMPLE: Pick a variant for each chat_id
Supports 3 approaches:
- control: base prompt (current)
- fsm: Finite State Machine
- structured: Structured Outputs
"""
import hashlib
import logging

logger = logging.getLogger(__name__)


class ExperimentManager:
    """
    Управляет A/B testing вариантами
    
    KISS principle: максимально просто
    """
    
    # Доступные варианты
    VARIANTS = {
        'control': 'Base Prompt (текущий)',
        'fsm': 'FSM с micro-prompts',
        'structured': 'Structured Outputs (OpenAI best practice)'
    }
    
    def __init__(self, force_variant: str = None):
        """
        Args:
            force_variant: Принудительный вариант для ВСЕХ (для тестирования)
                          Можно задать через env: EXPERIMENT_VARIANT=structured
        """
        self.force_variant = force_variant
        
        if force_variant:
            logger.info(f"🧪 EXPERIMENT: Force variant = {force_variant}")
    
    def get_variant(self, chat_id: str) -> str:
        """
        Определить вариант для chat_id
        
        Алгоритм:
        1. Если force_variant задан → возвращаем его
        2. Иначе: хешируем chat_id и делим 33%/33%/33%
        
        Args:
            chat_id: ID чата
        
        Returns:
            'control' | 'fsm' | 'structured'
        """
        # Force mode (для локального тестирования)
        if self.force_variant:
            return self.force_variant
        
        # Hash-based distribution (детерминированный)
        hash_value = int(hashlib.md5(chat_id.encode()).hexdigest(), 16)
        bucket = hash_value % 100  # 0-99
        
        if bucket < 33:
            return 'control'
        elif bucket < 66:
            return 'fsm'
        else:
            return 'structured'
    
    def should_use_control(self, chat_id: str) -> bool:
        """Использовать текущий (control) вариант?"""
        return self.get_variant(chat_id) == 'control'
    
    def should_use_fsm(self, chat_id: str) -> bool:
        """Использовать FSM?"""
        return self.get_variant(chat_id) == 'fsm'
    
    def should_use_structured(self, chat_id: str) -> bool:
        """Использовать Structured Outputs?"""
        return self.get_variant(chat_id) == 'structured'
    
    @classmethod
    def from_env(cls):
        """Создать из переменной окружения"""
        import os
        force = os.getenv('EXPERIMENT_VARIANT', None)
        
        if force and force not in cls.VARIANTS:
            logger.warning(f"Invalid EXPERIMENT_VARIANT={force}, ignoring")
            force = None
        
        return cls(force_variant=force)


# Singleton для удобства
_experiment_manager = None

def get_experiment_manager() -> ExperimentManager:
    """Получить глобальный менеджер экспериментов"""
    global _experiment_manager
    if _experiment_manager is None:
        _experiment_manager = ExperimentManager.from_env()
    return _experiment_manager


def set_force_variant(variant: str):
    """
    ТЕСТИРОВАНИЕ: принудительно установить вариант
    
    Usage в консоли:
        from chat.ai.experiment_manager import set_force_variant
        set_force_variant('structured')  # Все запросы → structured
    """
    global _experiment_manager
    
    if variant not in ExperimentManager.VARIANTS:
        raise ValueError(f"Unknown variant: {variant}. Available: {list(ExperimentManager.VARIANTS.keys())}")
    
    _experiment_manager = ExperimentManager(force_variant=variant)
    logger.info(f"🧪 Force variant set to: {variant}")
    print(f"✅ All chats will now use variant: {variant}")

