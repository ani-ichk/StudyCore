"""Модели для бд StudyCore."""
from .base import Base
from .user import User
from .role import Role, UserRole
from .student import Student, StudentParent
from .parent import Parent
from .group import Class
from .subject import Subject, TeacherSubject
from .homework import Homework
from .attendance import AttendanceLog
from .notification import Notification
from .meal import MealAccount, MealTransaction
from .book import Book, LibraryLoan
from .grade import Grade
from .room import Room
from .key import Key, KeyAllowedRole, KeyLog
from .schedule import Schedule
from .qr_code import QRCode
from .enums import NotificationType, EventType, RoomType, TransactionType