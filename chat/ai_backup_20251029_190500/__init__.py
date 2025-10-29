from .base import AvitoAIProcessor
from .extractors import CityExtractor, WorkDetailsExtractor
from .pricing import PricingCalculator
from .prompts import PromptBuilder
from .context import DialogueContextManager

__all__ = [
    'AvitoAIProcessor',
    'CityExtractor',
    'WorkDetailsExtractor',
    'PricingCalculator',
    'PromptBuilder',
    'DialogueContextManager',
]

SmartAIAssistant = AvitoAIProcessor

