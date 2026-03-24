import enum


class EventType(enum.Enum):
    IN = "IN"
    OUT = "OUT"


class TransactionType(enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


class RoomType(enum.Enum):
    CLASSROOM = "classroom"
    LIBRARY = "library"
    STORAGE = "storage_room"
    OTHER = "other"


class NotificationType(enum.Enum):
    ATTENDANCE = "attendance"
    GRADE = "grade"
    LIBRARY = "library"
    SCHEDULE = "schedule"
    MEAL = "meal"
    GENERAL = "general"