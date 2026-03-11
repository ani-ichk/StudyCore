"""Настройка базы данных и служебные программы."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from server.core.config import DB_URL, DB_DIR
from server.models.base import Base
from server.core.seed import seed_database

DB_DIR.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine = create_engine(DB_URL, connect_args=connect_args)
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
    Base.metadata.create_all(bind=engine)
    seed_database()
