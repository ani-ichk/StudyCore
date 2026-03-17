from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from models import AttendanceLog, User
from models.enums import EventType
from schemas import EventType as EventTypeSchema
from crud.add_methods import add_attendance_log


class AttendanceService:
    """Сервис для логики посещаемости."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def determine_event_type(self, user_id: int) -> Tuple[EventTypeSchema, EventType]:
        """
        Определение типа события (вход/выход) на основе последнего события.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Кортеж (схема события, модель события)
        """
        last_event = self.db.query(AttendanceLog)\
            .filter_by(user_id=user_id)\
            .order_by(AttendanceLog.timestamp.desc())\
            .first()
        
        if last_event and last_event.event_type == EventType.IN:
            # Если последнее событие - вход, то сейчас выход
            return EventTypeSchema.OUT, EventType.OUT
        else:
            # Если последнего события нет или был выход, то сейчас вход
            return EventTypeSchema.IN, EventType.IN
    
    def create_attendance_event(
        self, 
        user_id: int, 
        event_type: Optional[EventType] = None
    ) -> AttendanceLog:
        """
        Создание события посещаемости.
        
        Args:
            user_id: ID пользователя
            event_type: Тип события (если None, определяется автоматически)
            
        Returns:
            Объект AttendanceLog
        """
        if event_type is None:
            _, event_type = self.determine_event_type(user_id)
        
        attendance_log = AttendanceLog(
            user_id=user_id,
            event_type=event_type,
            timestamp=datetime.now()
        )
        
        self.db.add(attendance_log)
        self.db.commit()
        self.db.refresh(attendance_log)
        
        return attendance_log
    
    def get_last_event(self, user_id: int) -> Optional[AttendanceLog]:
        """
        Получение последнего события пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Последнее событие или None
        """
        return self.db.query(AttendanceLog)\
            .filter_by(user_id=user_id)\
            .order_by(AttendanceLog.timestamp.desc())\
            .first()
    
    def get_user_status(self, user_id: int) -> Dict[str, Any]:
        """
        Получение текущего статуса пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Словарь со статусом
        """
        user = self.db.query(User).get(user_id)
        if not user:
            return {
                'user_id': user_id,
                'status': 'unknown',
                'error': 'Пользователь не найден'
            }
        
        last_event = self.get_last_event(user_id)
        
        if not last_event:
            return {
                'user_id': user_id,
                'user_name': f"{user.surname} {user.name}",
                'status': 'unknown',
                'message': 'Нет данных о посещениях'
            }
        
        status = 'inside' if last_event.event_type == EventType.IN else 'outside'
        
        return {
            'user_id': user_id,
            'user_name': f"{user.surname} {user.name}",
            'status': status,
            'last_event': {
                'type': last_event.event_type.value,
                'timestamp': last_event.timestamp.isoformat()
            }
        }
    
    def create_manual_event(self, user_id: int, event_type: EventTypeSchema) -> AttendanceLog:
        """
        Ручное создание события (для администраторов).
        
        Args:
            user_id: ID пользователя
            event_type: Тип события
            
        Returns:
            Объект AttendanceLog
        """
        db_event_type = EventType.IN if event_type == EventTypeSchema.IN else EventType.OUT
        return self.create_attendance_event(user_id, db_event_type)
    
    def get_today_stats(self) -> Dict[str, Any]:
        """
        Получение статистики за сегодня.
        
        Returns:
            Словарь со статистикой
        """
        today_start = datetime.combine(datetime.now().date(), datetime.min.time())
        today_end = datetime.combine(datetime.now().date(), datetime.max.time())
        
        # Все события сегодня
        today_events = self.db.query(AttendanceLog)\
            .filter(
                AttendanceLog.timestamp >= today_start,
                AttendanceLog.timestamp <= today_end
            )\
            .all()
        
        # Уникальные пользователи
        user_ids = set(event.user_id for event in today_events)
        
        # Кто сейчас внутри
        currently_inside = []
        for user_id in user_ids:
            status = self.get_user_status(user_id)
            if status['status'] == 'inside':
                currently_inside.append({
                    'user_id': user_id,
                    'user_name': status['user_name'],
                    'last_event_time': status['last_event']['timestamp']
                })
        
        return {
            'date': datetime.now().date().isoformat(),
            'total_events': len(today_events),
            'unique_visitors': len(user_ids),
            'currently_inside': len(currently_inside),
            'visitors_list': currently_inside
        }