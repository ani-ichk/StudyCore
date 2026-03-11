from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from server.core.config import DB_URL
from .models import Base


class DatabaseManager:
    """Менеджер для работы с базой данных"""
    def __init__(self, db_url: str | None = None):
        if db_url is None:
            db_url = DB_URL
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        self.engine = create_engine(db_url, connect_args=connect_args)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Получить сессию для работы с БД"""
        return self.SessionLocal()