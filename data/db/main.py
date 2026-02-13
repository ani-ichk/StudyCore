from db_manager import DatabaseManager
from models import Role, User, UserRole, Subject


def initialize_database(db_manager):
    """Инициализация базы данных с начальными данными"""
    session = db_manager.get_session()
    try:
        # Создаем стандартные роли если их нет
        roles = ["admin", "teacher", "student", "parent", "staff"]
        for role_name in roles:
            if not session.query(Role).filter_by(name=role_name).first():
                session.add(Role(name=role_name))

        # Создаем тестовые предметы если их нет
        subjects = ["Математика", "Русский язык", "Физика", "Химия", "Биология",
                    "История", "Литература", "Иностранный язык", "Информатика"]
        for subject_name in subjects:
            if not session.query(Subject).filter_by(name=subject_name).first():
                session.add(Subject(name=subject_name))

        # Создаем администратора по умолчанию
        if not session.query(User).filter_by(login="admin").first():
            admin_user = User(
                login="admin",
                password="admin123",
                name="Администратор",
                patronymic="Системный",
                phone="+79000000000"
            )
            session.add(admin_user)
            session.flush()

            # Назначаем роль администратора
            admin_role = session.query(Role).filter_by(name="admin").first()
            if admin_role:
                session.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))

        session.commit()
        print("База данных инициализирована успешно")
    except Exception as e:
        session.rollback()
        print(f"Ошибка при инициализации БД: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    # Создание и инициализация базы данных
    db_manager = DatabaseManager()
    initialize_database(db_manager)
    print("Модели и менеджер базы данных готовы к использованию")