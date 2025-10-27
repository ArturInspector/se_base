"""
Автоматическая оценка качества AI ответов и диалогов

Принцип: каждый ответ оценивается по 4 параметрам:
1. Correctness (правильность данных)
2. Efficiency (не спрашивает лишнее)
3. Safety (соблюдение бизнес-правил)
4. Quality (естественность, краткость)

Score: 0.0 - 1.0
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class MessageGrade:
    """Оценка одного сообщения AI"""
    score: float  # 0.0-1.0
    correctness: float  # Правильность извлечения данных
    efficiency: float  # Эффективность (не спрашивает лишнее)
    safety: float  # Соблюдение бизнес-правил
    quality: float  # Качество текста
    
    # Flags
    has_hallucination: bool = False
    is_too_verbose: bool = False
    missed_opportunity: bool = False
    violated_business_rules: bool = False
    
    # Details
    issues: List[str] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []


@dataclass
class ConversationGrade:
    """Оценка целого диалога"""
    score: float  # 0-100
    outcome: str  # 'deal_created', 'client_left', 'handoff'
    total_messages: int
    messages_to_deal: Optional[int]
    unnecessary_questions: int
    issues: List[str]
    
    had_hallucinations: bool = False
    had_data_extraction_errors: bool = False
    had_business_rule_violations: bool = False


class ConversationGrader:
    """
    Автоматический грейдер для оценки качества диалогов
    """
    
    def __init__(self):
        self.business_rules = self._load_business_rules()
    
    def _load_business_rules(self) -> Dict:
        """Бизнес-правила для проверки"""
        return {
            "min_people": 2,
            "max_people_without_calc": 10,
            "min_hours": 1,
            "large_order_threshold": {"people": 5, "hours": 6},
            "forbidden_phrases": [
                "примерно",
                "около",
                "может быть",
                "не уверен",
                "сейчас уточню и вернусь"
            ],
            "required_in_first_message": [
                "ai-ассистент",
                "бета-тест",
                "тестирование"
            ]
        }
    
    def grade_message(
        self,
        user_message: str,
        ai_response: str,
        extracted_data: Dict,
        function_calls: List[Dict],
        context: Dict = None
    ) -> MessageGrade:
        """
        Оценить ОДНО сообщение AI
        
        Args:
            user_message: Сообщение от клиента
            ai_response: Ответ AI
            extracted_data: Извлеченные данные (city, people, hours, phone)
            function_calls: Какие функции вызвал AI
            context: Контекст (история диалога)
        
        Returns:
            MessageGrade с оценкой 0.0-1.0
        """
        issues = []
        
        # 1. CORRECTNESS (правильность извлечения данных)
        correctness = self._grade_correctness(
            user_message, extracted_data, issues
        )
        
        # 2. EFFICIENCY (не спрашивает лишнее)
        efficiency = self._grade_efficiency(
            user_message, ai_response, extracted_data, context, issues
        )
        
        # 3. SAFETY (соблюдение бизнес-правил)
        safety = self._grade_safety(
            extracted_data, ai_response, function_calls, issues
        )
        
        # 4. QUALITY (качество текста)
        quality = self._grade_quality(
            ai_response, context, issues
        )
        
        # Overall score (weighted average)
        score = (
            correctness * 0.35 +  # Правильность данных - важнее всего
            efficiency * 0.25 +   # Эффективность
            safety * 0.30 +       # Безопасность (бизнес-правила)
            quality * 0.10        # Качество текста
        )
        
        # Flags
        has_hallucination = any("галлюцинация" in issue.lower() for issue in issues)
        is_too_verbose = len(ai_response) > 400
        missed_opportunity = any("упустил" in issue.lower() for issue in issues)
        violated_business_rules = safety < 1.0
        
        return MessageGrade(
            score=score,
            correctness=correctness,
            efficiency=efficiency,
            safety=safety,
            quality=quality,
            has_hallucination=has_hallucination,
            is_too_verbose=is_too_verbose,
            missed_opportunity=missed_opportunity,
            violated_business_rules=violated_business_rules,
            issues=issues
        )
    
    def _grade_correctness(
        self,
        user_message: str,
        extracted_data: Dict,
        issues: List[str]
    ) -> float:
        """
        Оценка правильности извлечения данных
        
        Проверяет:
        - Правильно ли извлечен город
        - Правильно ли извлечены люди/часы
        - Нет ли фантазий (галлюцинаций)
        """
        score = 1.0
        message_lower = user_message.lower()
        
        # Проверка города
        if extracted_data.get('city'):
            city = extracted_data['city']
            
            # Город должен быть в сообщении (или в ad_data)
            if city.lower() not in message_lower:
                # Может быть из ad_data - это ОК
                pass
            
            # Проверка на область/район
            if any(word in city.lower() for word in ['область', 'район', 'округ']):
                issues.append("❌ Извлечен регион вместо города")
                score -= 0.3
        
        # Проверка people
        if extracted_data.get('people'):
            people = extracted_data['people']
            
            # Должно быть число в сообщении
            numbers = re.findall(r'\d+', message_lower)
            if str(people) not in numbers and people not in [int(n) for n in numbers]:
                issues.append(f"❌ Галлюцинация: люди={people} не в сообщении")
                score -= 0.5
            
            # Минимум 2
            if people < 2:
                issues.append(f"🔴 КРИТИЧНО: people={people} < 2")
                score = 0.0  # Автоматический провал
        
        # Проверка hours
        if extracted_data.get('hours'):
            hours = extracted_data['hours']
            numbers = re.findall(r'\d+', message_lower)
            
            if str(hours) not in numbers and hours not in [int(n) for n in numbers]:
                issues.append(f"❌ Галлюцинация: часы={hours} не в сообщении")
                score -= 0.4
        
        # Проверка телефона
        if extracted_data.get('phone'):
            phone = extracted_data['phone']
            phone_pattern = r'(\+7|8)?[\d\s\-\(\)]{10,15}'
            
            if not re.search(phone_pattern, user_message):
                issues.append("❌ Галлюцинация: телефон не в сообщении")
                score -= 0.6
        
        return max(0.0, score)
    
    def _grade_efficiency(
        self,
        user_message: str,
        ai_response: str,
        extracted_data: Dict,
        context: Optional[Dict],
        issues: List[str]
    ) -> float:
        """
        Оценка эффективности (не спрашивает лишнее)
        
        Проверяет:
        - Не спрашивает то, что уже есть
        - Не задает несколько вопросов сразу
        - Использует function calling когда нужно
        """
        score = 1.0
        
        # Клиент дал телефон - AI должен создать сделку
        phone_in_message = bool(re.search(r'(\+7|8)?\d{10}', user_message))
        if phone_in_message and 'create_bitrix_deal' not in str(extracted_data):
            issues.append("⚠️ Упустил возможность: телефон есть, но сделка не создана")
            score -= 0.4
        
        # Спрашивает то что уже есть?
        if extracted_data.get('city') and 'город' in ai_response.lower():
            issues.append("⚠️ Спрашивает город, хотя он уже известен")
            score -= 0.3
        
        # Несколько вопросов сразу?
        questions = ai_response.count('?')
        if questions > 1:
            issues.append(f"⚠️ Задает {questions} вопросов сразу (нужен 1)")
            score -= 0.2
        
        # Должен вызвать get_city_pricing если город известен
        if extracted_data.get('city') and not extracted_data.get('ppr'):
            if 'get_city_pricing' not in str(context or {}):
                issues.append("⚠️ Не вызвал get_city_pricing для известного города")
                score -= 0.3
        
        return max(0.0, score)
    
    def _grade_safety(
        self,
        extracted_data: Dict,
        ai_response: str,
        function_calls: List[Dict],
        issues: List[str]
    ) -> float:
        """
        Оценка соблюдения бизнес-правил
        
        Проверяет:
        - Минимум 2 грузчика
        - Цены только из get_city_pricing
        - Юрлица: уточнил ли статус для больших заказов
        """
        score = 1.0
        
        # Правило 1: минимум 2 грузчика
        if extracted_data.get('people') and extracted_data['people'] < 2:
            issues.append("🔴 КРИТИЧНО: Нарушение правила минимум 2 грузчика")
            return 0.0  # Автопровал
        
        # Правило 2: Цены только из функций
        price_pattern = r'\d{3,5}\s*₽'
        if re.search(price_pattern, ai_response):
            # Есть цена в ответе - должна быть из get_city_pricing
            has_get_pricing = any(
                fc.get('function') == 'get_city_pricing' 
                for fc in function_calls
            )
            if not has_get_pricing:
                issues.append("❌ Галлюцинация цены: не вызвал get_city_pricing")
                score -= 0.6
        
        # Правило 3: Большие заказы - уточнить юрлицо
        people = extracted_data.get('people', 0)
        hours = extracted_data.get('hours', 0)
        
        if (people >= 5 or hours >= 6) and not extracted_data.get('is_legal_entity'):
            if 'компани' not in ai_response.lower() and 'юр' not in ai_response.lower():
                issues.append("⚠️ Большой заказ: не уточнил компания/частный")
                score -= 0.3
        
        # Правило 4: Не должен обещать что-то без подтверждения
        forbidden = self.business_rules['forbidden_phrases']
        for phrase in forbidden:
            if phrase in ai_response.lower():
                issues.append(f"⚠️ Неуверенная формулировка: '{phrase}'")
                score -= 0.2
                break
        
        return max(0.0, score)
    
    def _grade_quality(
        self,
        ai_response: str,
        context: Optional[Dict],
        issues: List[str]
    ) -> float:
        """
        Оценка качества текста
        
        Проверяет:
        - Длина ответа (1-2 предложения)
        - Наличие disclaimer в первом сообщении
        - Естественность
        """
        score = 1.0
        
        # Длина (оптимум: 50-300 символов)
        length = len(ai_response)
        if length > 400:
            issues.append(f"⚠️ Слишком длинный ответ ({length} символов)")
            score -= 0.3
        elif length < 30:
            issues.append("⚠️ Слишком короткий ответ")
            score -= 0.2
        
        # Первое сообщение: должен быть disclaimer
        is_first = not context or len(context.get('history', [])) == 0
        if is_first:
            required = self.business_rules['required_in_first_message']
            has_disclaimer = any(
                phrase in ai_response.lower() 
                for phrase in required
            )
            if not has_disclaimer:
                issues.append("⚠️ Нет disclaimer об AI в первом сообщении")
                score -= 0.4
        
        # Естественность (проверка на шаблонность)
        if ai_response.count('•') > 3 or ai_response.count('\n') > 4:
            issues.append("⚠️ Слишком структурированный (списки/перечисления)")
            score -= 0.2
        
        return max(0.0, score)
    
    def grade_conversation(
        self,
        chat_id: str,
        messages: List[Dict],
        deal_created: bool = False,
        deal_id: Optional[int] = None
    ) -> ConversationGrade:
        """
        Оценить весь диалог целиком
        
        Args:
            chat_id: ID чата
            messages: Список сообщений диалога
            deal_created: Создана ли сделка
            deal_id: ID сделки
        
        Returns:
            ConversationGrade с оценкой 0-100
        """
        issues = []
        total_messages = len(messages)
        
        # Outcome
        if deal_created:
            outcome = "deal_created"
        elif total_messages == 0:
            outcome = "no_messages"
        elif total_messages == 1:
            outcome = "client_left_immediately"
        else:
            outcome = "client_left"
        
        # Сколько сообщений понадобилось для сделки
        messages_to_deal = None
        if deal_created:
            messages_to_deal = total_messages
            
            # Идеально: 1-3 сообщения
            if messages_to_deal <= 3:
                issues.append("✅ Отлично: сделка за 1-3 сообщения")
            elif messages_to_deal <= 5:
                issues.append("✔️ Хорошо: сделка за 4-5 сообщений")
            else:
                issues.append(f"⚠️ Долго: {messages_to_deal} сообщений до сделки")
        
        # Лишние переспросы (эвристика)
        unnecessary_questions = 0
        for msg in messages:
            if msg.get('role') == 'assistant' and msg.get('content'):
                # Спрашивает несколько вещей сразу?
                if msg['content'].count('?') > 1:
                    unnecessary_questions += 1
        
        # Проверка наличия проблем
        had_hallucinations = any(
            msg.get('has_hallucination', False) 
            for msg in messages
        )
        
        had_data_extraction_errors = any(
            msg.get('correctness', 1.0) < 0.7
            for msg in messages if 'correctness' in msg
        )
        
        had_business_rule_violations = any(
            msg.get('violated_business_rules', False)
            for msg in messages
        )
        
        # Подсчет score (0-100)
        score = 100.0
        
        if not deal_created:
            score -= 50  # Не создана сделка = -50 баллов
        
        if messages_to_deal and messages_to_deal > 5:
            score -= (messages_to_deal - 5) * 5  # -5 за каждое лишнее
        
        if had_hallucinations:
            score -= 20
        
        if had_business_rule_violations:
            score -= 30
        
        if unnecessary_questions > 0:
            score -= unnecessary_questions * 5
        
        score = max(0.0, min(100.0, score))
        
        return ConversationGrade(
            score=score,
            outcome=outcome,
            total_messages=total_messages,
            messages_to_deal=messages_to_deal,
            unnecessary_questions=unnecessary_questions,
            issues=issues,
            had_hallucinations=had_hallucinations,
            had_data_extraction_errors=had_data_extraction_errors,
            had_business_rule_violations=had_business_rule_violations
        )


