"""Настройка базы данных и служебные программы."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .config import DB_URL, DB_DIR
from models.base import Base
from .seed import seed_database

DB_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Возвращает сеанс SQLAlchemy для запроса."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Инициализируйте базу данных, создав все таблицы и заполнив их данными по умолчанию."""
    import models
    
    tables = [
        models.User.__table__,
        models.Role.__table__,
        models.Room.__table__,
        models.Subject.__table__,
        models.UserRole.__table__,
        models.Student.__table__,
        models.Parent.__table__,
        models.StudentParent.__table__,
        models.Class.__table__,
        models.TeacherSubject.__table__,
        models.Grade.__table__,
        models.Homework.__table__,
        models.AttendanceLog.__table__,
        models.Notification.__table__,
        models.MealAccount.__table__,
        models.MealTransaction.__table__,
        models.Book.__table__,
        models.LibraryLoan.__table__,
        models.Key.__table__,
        models.KeyAllowedRole.__table__,
        models.KeyLog.__table__,
        models.Schedule.__table__,
        models.QRCode.__table__
    ]

    Base.metadata.create_all(bind=engine, tables=tables)
    
    session = SessionLocal()
    try:
        seed_database(session)
    finally:
        session.close()
