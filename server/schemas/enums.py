from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"
    STAFF = "staff"


class QRCodePurpose(str, Enum):
    ATTENDANCE = "attendance"
    LIBRARY = "library"
    MEAL = "meal"
    ENTRANCE = "entrance"


class EventType(str, Enum):
    IN = "IN"
    OUT = "OUT"