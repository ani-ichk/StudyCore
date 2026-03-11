"""Модели для бд StudyCore."""
from server.models.base import Base
from server.models.user import User
from server.models.role import Role, UserRole
from server.models.student import Student, StudentParent
from server.models.parent import Parent
from server.models.group import Class
from server.models.subject import Subject, TeacherSubject
from server.models.homework import Homework
from server.models.attendance import AttendanceLog
from server.models.notification import Notification
from server.models.meal import MealAccount, MealTransaction
from server.models.book import Book, LibraryLoan
from server.models.grade import Grade
from server.models.room import Room
from server.models.key import Key, KeyAllowedRole, KeyLog
from server.models.schedule import Schedule
from server.models.qr_code import QRCode
from server.models.enums import NotificationType, EventType, RoomType, TransactionType