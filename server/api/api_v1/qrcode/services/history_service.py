from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from models import AttendanceLog, User
from models.enums import EventType
from schemas import AttendanceHistoryItem


class HistoryService:
    """Сервис для работы с историей посещений."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_history(
        self,
        user_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AttendanceLog]:
        """
        Получение истории посещений пользователя.
        
        Args:
            user_id: ID пользователя
            date_from: Начальная дата
            date_to: Конечная дата
            limit: Лимит записей
            offset: Смещение для пагинации
            
        Returns:
            Список событий
        """
        query = self.db.query(AttendanceLog).filter_by(user_id=user_id)
        
        if date_from:
            query = query.filter(
                AttendanceLog.timestamp >= datetime.combine(date_from, datetime.min.time())
            )
        
        if date_to:
            query = query.filter(
                AttendanceLog.timestamp <= datetime.combine(date_to, datetime.max.time())
            )
        
        return query.order_by(AttendanceLog.timestamp.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
    
    def get_user_history_count(
        self,
        user_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> int:
        """
        Получение количества записей истории пользователя.
        
        Args:
            user_id: ID пользователя
            date_from: Начальная дата
            date_to: Конечная дата
            
        Returns:
            Количество записей
        """
        query = self.db.query(AttendanceLog).filter_by(user_id=user_id)
        
        if date_from:
            query = query.filter(
                AttendanceLog.timestamp >= datetime.combine(date_from, datetime.min.time())
            )
        
        if date_to:
            query = query.filter(
                AttendanceLog.timestamp <= datetime.combine(date_to, datetime.max.time())
            )
        
        return query.count()
    
    def format_history_items(self, events: List[AttendanceLog]) -> List[AttendanceHistoryItem]:
        """
        Форматирование событий в схему ответа.
        
        Args:
            events: Список событий
            
        Returns:
            Список AttendanceHistoryItem
        """
        return [
            AttendanceHistoryItem(
                id=event.id,
                event_type=event.event_type.value,
                timestamp=event.timestamp
            )
            for event in events
        ]
    
    def get_attendance_summary(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Получение сводной статистики по посещаемости.
        
        Args:
            user_id: ID пользователя
            days: Количество дней для анализа
            
        Returns:
            Словарь со статистикой
        """
        user = self.db.query(User).get(user_id)
        if not user:
            return {'error': 'Пользователь не найден'}
        
        start_date = datetime.now() - timedelta(days=days)
        
        # Получаем все события за период
        events = self.db.query(AttendanceLog)\
            .filter(
                and_(
                    AttendanceLog.user_id == user_id,
                    AttendanceLog.timestamp >= start_date
                )
            )\
            .order_by(AttendanceLog.timestamp)\
            .all()
        
        # Анализируем
        total_ins = sum(1 for e in events if e.event_type == EventType.IN)
        total_outs = sum(1 for e in events if e.event_type == EventType.OUT)
        
        # Группируем по дням
        daily_stats = {}
        for event in events:
            day = event.timestamp.date()
            if day not in daily_stats:
                daily_stats[day] = {"in": 0, "out": 0}
            
            if event.event_type == EventType.IN:
                daily_stats[day]["in"] += 1
            else:
                daily_stats[day]["out"] += 1
        
        return {
            "user_id": user_id,
            "user_name": f"{user.surname} {user.name}",
            "period_days": days,
            "date_from": start_date.date().isoformat(),
            "date_to": datetime.now().date().isoformat(),
            "total_events": len(events),
            "total_entries": total_ins,
            "total_exits": total_outs,
            "daily_stats": [
                {
                    "date": day.isoformat(),
                    "entries": stats["in"],
                    "exits": stats["out"]
                }
                for day, stats in sorted(daily_stats.items())
            ]
        }
    
    def get_range_history(
        self,
        date_from: date,
        date_to: date,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Получение истории за диапазон дат.
        
        Args:
            date_from: Начальная дата
            date_to: Конечная дата
            user_id: ID пользователя для фильтрации
            
        Returns:
            Словарь со статистикой по пользователям
        """
        query = self.db.query(AttendanceLog).filter(
            AttendanceLog.timestamp >= datetime.combine(date_from, datetime.min.time()),
            AttendanceLog.timestamp <= datetime.combine(date_to, datetime.max.time())
        )
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        events = query.order_by(AttendanceLog.timestamp).all()
        
        # Группируем по пользователям
        users_stats = {}
        for event in events:
            if event.user_id not in users_stats:
                user = self.db.query(User).get(event.user_id)
                users_stats[event.user_id] = {
                    "user_name": f"{user.surname} {user.name}" if user else "Неизвестный",
                    "entries": 0,
                    "exits": 0,
                    "events": []
                }
            
            if event.event_type == EventType.IN:
                users_stats[event.user_id]["entries"] += 1
            else:
                users_stats[event.user_id]["exits"] += 1
            
            users_stats[event.user_id]["events"].append({
                "id": event.id,
                "type": event.event_type.value,
                "timestamp": event.timestamp.isoformat()
            })
        
        return {
            "date_range": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat()
            },
            "total_events": len(events),
            "total_users": len(users_stats),
            "users": users_stats
        }