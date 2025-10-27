"""
FSM (Finite State Machine) для управления диалогом

Архитектура:
- states.py: Определения состояний и контекста
- transitions.py: Логика переходов между состояниями
- micro_prompts.py: Микро-промпты для каждого состояния
- state_machine.py: Главный контроллер FSM
"""

from .states import DialogueState, StateContext
from .state_machine import DialogueStateMachine
from .validators import get_metrics_collector

__all__ = ['DialogueState', 'StateContext', 'DialogueStateMachine', 'get_metrics_collector']

