from .db_manager import DatabaseManager


# Глобальный менеджер базы данных (SQLAlchemy)
# Импортируйте `db_manager`, `engine`, `SessionLocal` из этого модуля
# чтобы использовать единый объект подключения по всему приложению.
#
# Пример:
#   from data.db.main import db_manager
#   session = db_manager.get_session()

db_manager = DatabaseManager()
engine = db_manager.engine
SessionLocal = db_manager.SessionLocal