"""
Определения состояний FSM и контекста диалога

SRP: Только структуры данных, никакой логики
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import time


class DialogueState(str, Enum):
    """
    Состояния диалога
    
    Каждое состояние = один шаг в диалоге
    """
    GREETING = "greeting"                    # Приветствие + определение намерения
    INTENT_CLASSIFICATION = "classification" # Уточнение: цена? заказ? вопрос?
    CITY_INQUIRY = "city_inquiry"           # Узнать город
    PRICE_INQUIRY = "price_inquiry"         # Консультация по ценам
    BOOKING_COLLECTION = "booking"          # Сбор данных для заказа
    BOOKING_CONFIRMATION = "confirmation"   # Подтверждение + создание сделки
    ISSUE_RESOLUTION = "issue"              # Решение проблем/вопросов
    HANDOFF_OPERATOR = "handoff"            # Передача оператору (персональный расчет)
    WAITING_RESPONSE = "waiting"            # Ожидание ответа клиента
    COMPLETED = "completed"                 # Диалог завершен


@dataclass
class StateContext:
    """
    Контекст диалога - данные собранные в процессе
    
    Принцип: Single Source of Truth для состояния диалога
    """
    current_state: DialogueState
    chat_id: str
    
    # Собранные данные для заказа
    city: Optional[str] = None
    hours: Optional[int] = None
    people: Optional[int] = None
    phone: Optional[str] = None
    work_type: Optional[str] = None
    is_legal_entity: Optional[bool] = None
    company_name: Optional[str] = None
    
    # Распознанное намерение
    intent: Optional[str] = None  # "price", "booking", "question"
    
    # Метаданные
    last_message_time: float = field(default_factory=time.time)
    retry_count: int = 0          # Сколько раз переспрашивали
    fallback_count: int = 0       # Сколько раз не поняли
    
    # Флаги специальных случаев
    is_takelage: bool = False              # Такелаж (>100кг)
    is_out_of_city: bool = False           # За город
    requires_personal_calc: bool = False   # Нужен персональный расчет
    needs_legal_clarification: bool = False # Нужно уточнить: компания или частный?
    
    # Прайс из get_city_pricing
    ppr: Optional[int] = None              # Price per hour
    min_hours: Optional[float] = None      # Минимум часов
    
    def to_dict(self) -> Dict[str, Any]:
        """Для сериализации в БД"""
        return {
            "state": self.current_state.value,
            "city": self.city,
            "hours": self.hours,
            "people": self.people,
            "phone": self.phone,
            "work_type": self.work_type,
            "is_legal_entity": self.is_legal_entity,
            "company_name": self.company_name,
            "intent": self.intent,
            "retry_count": self.retry_count,
            "fallback_count": self.fallback_count,
            "is_takelage": self.is_takelage,
            "is_out_of_city": self.is_out_of_city,
            "requires_personal_calc": self.requires_personal_calc,
            "needs_legal_clarification": self.needs_legal_clarification,
            "ppr": self.ppr,
            "min_hours": self.min_hours,
            "last_message_time": self.last_message_time
        }
    
    @classmethod
    def from_dict(cls, chat_id: str, data: Dict[str, Any]) -> 'StateContext':
        """Восстановить из словаря (из БД)"""
        return cls(
            current_state=DialogueState(data.get("state", "greeting")),
            chat_id=chat_id,
            city=data.get("city"),
            hours=data.get("hours"),
            people=data.get("people"),
            phone=data.get("phone"),
            work_type=data.get("work_type"),
            is_legal_entity=data.get("is_legal_entity"),
            company_name=data.get("company_name"),
            intent=data.get("intent"),
            retry_count=data.get("retry_count", 0),
            fallback_count=data.get("fallback_count", 0),
            is_takelage=data.get("is_takelage", False),
            is_out_of_city=data.get("is_out_of_city", False),
            requires_personal_calc=data.get("requires_personal_calc", False),
            needs_legal_clarification=data.get("needs_legal_clarification", False),
            ppr=data.get("ppr"),
            min_hours=data.get("min_hours"),
            last_message_time=data.get("last_message_time", time.time())
        )
    
    def has_minimum_data(self) -> bool:
        """Есть ли минимум данных для расчета цены"""
        return bool(self.city and self.people)
    
    def has_complete_booking_data(self) -> bool:
        """Есть ли все данные для создания сделки"""
        return bool(self.phone and self.city and self.people and self.hours)
    
    def should_ask_legal_status(self) -> bool:
        """Нужно ли уточнить: компания или частное лицо?"""
        # >= 5 грузчиков или >= 6 часов → уточнить
        large_order = (self.people and self.people >= 5) or (self.hours and self.hours >= 6)
        return large_order and self.is_legal_entity is None
    
    def reset_retry_counters(self):
        """Сбросить счетчики после успешного шага"""
        self.retry_count = 0
        self.fallback_count = 0

