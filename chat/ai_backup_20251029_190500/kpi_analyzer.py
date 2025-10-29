"""
KPI Analyzer - анализ метрик AI бота

Собирает статистику:
- Конверсия (% диалогов → сделка)
- Качество (средний score)
- Проблемы (галлюцинации, ошибки)
- A/B testing сравнение
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from db import Session
from chats_log.entities import ChatLog, ConversationGrade

logger = logging.getLogger(__name__)


class KPIAnalyzer:
    """
    Анализатор KPI метрик AI бота
    """
    
    def get_dashboard_metrics(
        self,
        hours: int = 24,
        experiment_variant: Optional[str] = None
    ) -> Dict:
        """
        Получить метрики для dashboard
        
        Args:
            hours: За сколько часов (по умолчанию 24)
            experiment_variant: Фильтр по варианту эксперимента
        
        Returns:
            Dict с метриками
        """
        since = datetime.now() - timedelta(hours=hours)
        
        with Session() as session:
            # Base query
            query = session.query(ChatLog).filter(
                ChatLog.created_at >= since
            )
            
            if experiment_variant:
                query = query.filter(
                    ChatLog.experiment_variant == experiment_variant
                )
            
            # 1. Общие метрики
            total_messages = query.count()
            
            # 2. Сделки
            deals_created = query.filter(
                ChatLog.deal_created == True
            ).count()
            
            # 3. Качество
            avg_quality = session.query(
                func.avg(ChatLog.quality_score)
            ).filter(
                ChatLog.created_at >= since,
                ChatLog.quality_score != None
            ).scalar() or 0.0
            
            # 4. Проблемы
            hallucinations = query.filter(
                ChatLog.has_hallucination == True
            ).count()
            
            # 5. Unique chats
            unique_chats = session.query(
                func.count(func.distinct(ChatLog.chat_id))
            ).filter(
                ChatLog.created_at >= since
            ).scalar()
            
            # 6. Conversion rate (conversations)
            conversation_query = session.query(ConversationGrade).filter(
                ConversationGrade.created_at >= since
            )
            
            if experiment_variant:
                conversation_query = conversation_query.filter(
                    ConversationGrade.experiment_variant == experiment_variant
                )
            
            total_conversations = conversation_query.count()
            successful_conversations = conversation_query.filter(
                ConversationGrade.outcome == 'deal_created'
            ).count()
            
            conversion_rate = (
                (successful_conversations / total_conversations * 100)
                if total_conversations > 0 else 0.0
            )
            
            # 7. Avg messages to deal
            avg_messages_to_deal = session.query(
                func.avg(ConversationGrade.messages_to_deal)
            ).filter(
                ConversationGrade.created_at >= since,
                ConversationGrade.outcome == 'deal_created'
            ).scalar() or 0.0
            
            # 8. Response time
            avg_response_time = session.query(
                func.avg(ChatLog.response_time_ms)
            ).filter(
                ChatLog.created_at >= since,
                ChatLog.response_time_ms != None
            ).scalar() or 0.0
            
            return {
                "period": f"Last {hours} hours",
                "total_messages": total_messages,
                "unique_conversations": unique_chats,
                "total_conversations_graded": total_conversations,
                
                "deals": {
                    "created": deals_created,
                    "conversion_rate": round(conversion_rate, 2),
                    "avg_messages_to_deal": round(avg_messages_to_deal, 2)
                },
                
                "quality": {
                    "avg_score": round(avg_quality, 3),
                    "hallucinations": hallucinations,
                    "hallucination_rate": round(
                        (hallucinations / total_messages * 100) if total_messages > 0 else 0.0,
                        2
                    )
                },
                
                "performance": {
                    "avg_response_time_ms": round(avg_response_time, 0),
                    "avg_response_time_sec": round(avg_response_time / 1000, 2)
                },
                
                "experiment_variant": experiment_variant or "all"
            }
    
    def get_top_issues(
        self,
        hours: int = 24,
        limit: int = 10
    ) -> List[Dict]:
        """
        Топ проблем за период
        
        Returns:
            List[Dict]: Топ проблем с количеством
        """
        since = datetime.now() - timedelta(hours=hours)
        
        with Session() as session:
            # Группируем по failure_reason
            issues = session.query(
                ChatLog.failure_reason,
                func.count(ChatLog.id).label('count')
            ).filter(
                ChatLog.created_at >= since,
                ChatLog.failure_reason != None
            ).group_by(
                ChatLog.failure_reason
            ).order_by(
                func.count(ChatLog.id).desc()
            ).limit(limit).all()
            
            return [
                {"issue": issue, "count": count}
                for issue, count in issues
            ]
    
    def get_conversation_distribution(
        self,
        hours: int = 24
    ) -> Dict:
        """
        Распределение диалогов по результатам
        
        Returns:
            Dict: outcome -> count
        """
        since = datetime.now() - timedelta(hours=hours)
        
        with Session() as session:
            distribution = session.query(
                ConversationGrade.outcome,
                func.count(ConversationGrade.id).label('count')
            ).filter(
                ConversationGrade.created_at >= since
            ).group_by(
                ConversationGrade.outcome
            ).all()
            
            return {
                outcome: count
                for outcome, count in distribution
            }
    
    def compare_experiments(
        self,
        variant_a: str,
        variant_b: str,
        hours: int = 24
    ) -> Dict:
        """
        A/B testing: сравнение двух вариантов
        
        Args:
            variant_a: Вариант A (например "control")
            variant_b: Вариант B (например "structured_outputs")
            hours: За сколько часов
        
        Returns:
            Dict с сравнением метрик
        """
        metrics_a = self.get_dashboard_metrics(hours, variant_a)
        metrics_b = self.get_dashboard_metrics(hours, variant_b)
        
        # Вычисляем разницу
        conversion_diff = (
            metrics_b['deals']['conversion_rate'] - 
            metrics_a['deals']['conversion_rate']
        )
        
        quality_diff = (
            metrics_b['quality']['avg_score'] -
            metrics_a['quality']['avg_score']
        )
        
        messages_diff = (
            metrics_b['deals']['avg_messages_to_deal'] -
            metrics_a['deals']['avg_messages_to_deal']
        )
        
        # Winner
        if conversion_diff > 5:  # >5% улучшение
            winner = variant_b
            confidence = "high"
        elif conversion_diff > 2:
            winner = variant_b
            confidence = "medium"
        elif conversion_diff < -5:
            winner = variant_a
            confidence = "high"
        elif conversion_diff < -2:
            winner = variant_a
            confidence = "medium"
        else:
            winner = "tie"
            confidence = "low"
        
        return {
            "variant_a": {
                "name": variant_a,
                "metrics": metrics_a
            },
            "variant_b": {
                "name": variant_b,
                "metrics": metrics_b
            },
            "comparison": {
                "conversion_rate_diff": round(conversion_diff, 2),
                "conversion_rate_improvement": f"{conversion_diff:+.2f}%",
                "quality_score_diff": round(quality_diff, 3),
                "avg_messages_diff": round(messages_diff, 2),
                "winner": winner,
                "confidence": confidence
            },
            "recommendation": self._generate_recommendation(
                conversion_diff, quality_diff, messages_diff, winner
            )
        }
    
    def _generate_recommendation(
        self,
        conversion_diff: float,
        quality_diff: float,
        messages_diff: float,
        winner: str
    ) -> str:
        """Генерация рекомендации на основе метрик"""
        
        if winner == "tie":
            return "Нет значимой разницы. Нужно больше данных или изменения недостаточно сильны."
        
        reasons = []
        
        if abs(conversion_diff) > 5:
            reasons.append(f"конверсия {'выше' if conversion_diff > 0 else 'ниже'} на {abs(conversion_diff):.1f}%")
        
        if abs(quality_diff) > 0.1:
            reasons.append(f"качество {'лучше' if quality_diff > 0 else 'хуже'} на {abs(quality_diff):.2f}")
        
        if abs(messages_diff) > 1:
            reasons.append(f"{'меньше' if messages_diff < 0 else 'больше'} сообщений до сделки")
        
        recommendation = f"✅ Вариант '{winner}' показывает лучшие результаты: {', '.join(reasons)}."
        
        if len(reasons) >= 2:
            recommendation += " Рекомендуется перейти на этот вариант в production."
        else:
            recommendation += " Продолжить тестирование для подтверждения."
        
        return recommendation
    
    def get_recent_conversations(
        self,
        limit: int = 20,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None
    ) -> List[Dict]:
        """
        Получить последние диалоги для ручной проверки
        
        Args:
            limit: Сколько диалогов
            min_score: Минимальный score (для фильтрации плохих)
            max_score: Максимальный score (для фильтрации хороших)
        
        Returns:
            List[Dict]: Диалоги с оценками
        """
        with Session() as session:
            query = session.query(ConversationGrade).order_by(
                ConversationGrade.created_at.desc()
            )
            
            if min_score is not None:
                query = query.filter(
                    ConversationGrade.conversation_score >= min_score
                )
            
            if max_score is not None:
                query = query.filter(
                    ConversationGrade.conversation_score <= max_score
                )
            
            conversations = query.limit(limit).all()
            
            result = []
            for conv in conversations:
                # Получить сообщения этого диалога
                messages = session.query(ChatLog).filter(
                    ChatLog.chat_id == conv.chat_id
                ).order_by(ChatLog.created_at).all()
                
                result.append({
                    "chat_id": conv.chat_id,
                    "score": round(conv.conversation_score, 2),
                    "outcome": conv.outcome,
                    "total_messages": conv.total_messages,
                    "messages_to_deal": conv.messages_to_deal,
                    "had_issues": (
                        conv.had_hallucinations or 
                        conv.had_data_extraction_errors or 
                        conv.had_business_rule_violations
                    ),
                    "duration_minutes": conv.duration_minutes,
                    "messages": [
                        {
                            "role": "user" if msg.author_id != msg.user_id else "assistant",
                            "content": msg.message if msg.author_id != msg.user_id else msg.answer,
                            "quality_score": msg.quality_score
                        }
                        for msg in messages
                    ],
                    "created_at": conv.created_at.isoformat() if conv.created_at else None
                })
            
            return result

