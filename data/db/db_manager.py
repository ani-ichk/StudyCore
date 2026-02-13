from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base


class DatabaseManager:
    """Менеджер для работы с базой данных"""

    def __init__(self, db_url="sqlite:///school_system.db"):
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Получить сессию для работы с БД"""
        return self.SessionLocal()