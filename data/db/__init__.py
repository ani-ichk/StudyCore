from models import (
    Base, User, Role, UserRole, QRCode, Parent, Student, StudentParent,
    Class, Subject, TeacherSubject, Homework, AttendanceLog, Notification,
    MealAccount, MealTransaction, Book, LibraryLoan, Grade, Room, Key,
    KeyAllowedRole, KeyLog, Schedule, EventType, TransactionType,
    RoomType, NotificationType
)

# Экспортируем менеджер
from db_manager import DatabaseManager

# Экспортируем методы как модули
from . import add_methods
from . import read_methods
from . import update_methods
from . import delete_methods
from . import auth_methods
from . import utils

# Создаем удобные алиасы
add = add_methods
read = read_methods
update = update_methods
delete = delete_methods
auth = auth_methods