from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from schemas import UserCreate, UserResponse, UserRole
from crud.add_methods import (
    add_user_with_roles, add_student_with_account, 
    add_parent, add_role_to_user
)
from crud.read_methods import get_user_by_login, get_user_roles
from models import Role, User, Student, Parent
from scripts.security import PasswordHasher

router = APIRouter(prefix="/register", tags=["registration"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Регистрация нового пользователя с множественными ролями.
    
    - Поддерживает назначение нескольких ролей одновременно
    - Автоматически создает связанные записи (студент, родитель и т.д.)
    - Проверяет сложность пароля
    """
    # Проверяем, не существует ли пользователь с таким логином
    existing_user = get_user_by_login(db, user_data.login)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким логином уже существует"
        )
    
    # Проверяем сложность пароля
    if not PasswordHasher.is_password_strong(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пароль слишком слабый. Используйте минимум 8 символов, заглавные и строчные буквы, цифры и спецсимволы"
        )
    
    # Проверяем существование указанных ролей
    valid_roles = []
    for role_name in user_data.role_names:
        role = db.query(Role).filter_by(name=role_name).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Роль '{role_name}' не существует. Доступные роли: admin, teacher, student, parent, staff"
            )
        valid_roles.append(role)
    
    try:
        # Создаем пользователя с ролями
        user = add_user_with_roles(
            session=db,
            login=user_data.login,
            password=user_data.password,
            surname=user_data.surname,
            name=user_data.name,
            role_names=user_data.role_names,
            patronymic=user_data.patronymic,
            phone=user_data.phone,
            email=user_data.email
        )
        
        # Создаем дополнительные записи в зависимости от ролей
        if "student" in user_data.role_names:
            # Для студента нужно указать класс (в реальном приложении получаем из запроса)
            class_id = 1  # Временное значение
            student = add_student_with_account(db, user.id, class_id, initial_balance=100.0)
            
        if "parent" in user_data.role_names:
            parent = add_parent(db, user.id)
            
        # Если пользователь и студент, и родитель (тьютор), создаем обе записи
        if "teacher" in user_data.role_names:
            # Для учителя дополнительные настройки
            pass
            
        if "admin" in user_data.role_names:
            # Для администратора дополнительные права
            pass
        
        db.commit()
        
        # Получаем обновленного пользователя со всеми связями
        user = db.query(User).get(user.id)
        
        # Формируем ответ
        response = UserResponse(
            id=user.id,
            login=user.login,
            surname=user.surname,
            name=user.name,
            patronymic=user.patronymic,
            phone=user.phone,
            email=user.email,
            is_active=user.is_active,
            roles=[role.name for role in user.roles]
        )
        
        return response
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при регистрации: {str(e)}"
        )


@router.post("/with-children", response_model=UserResponse)
async def register_parent_with_children(
    user_data: UserCreate,
    children_ids: List[int] = Body(..., description="ID студентов, к которым привязывается родитель"),
    db: Session = Depends(get_db)
):
    """
    Регистрация родителя с привязкой к существующим студентам.
    """
    # Сначала регистрируем пользователя
    user = await register_user(user_data, db)
    
    # Находим запись родителя
    parent = db.query(Parent).filter_by(user_id=user.id).first()
    if not parent:
        # Если роль parent не была указана, добавляем её
        role = db.query(Role).filter_by(name="parent").first()
        if role:
            add_role_to_user(db, user.id, role.id)
            parent = add_parent(db, user.id)
    
    # Привязываем детей
    if parent:
        for child_id in children_ids:
            student = db.query(Student).get(child_id)
            if student and student not in parent.students:
                parent.students.append(student)
        
        db.commit()
    
    return user


@router.post("/batch", response_model=List[UserResponse])
async def register_multiple_users(
    users_data: List[UserCreate],
    db: Session = Depends(get_db)
):
    """
    Массовая регистрация пользователей (для администраторов).
    """
    registered_users = []
    
    for user_data in users_data:
        try:
            user = await register_user(user_data, db)
            registered_users.append(user)
        except HTTPException as e:
            # Пропускаем ошибки и продолжаем с другими пользователями
            continue
    
    return registered_users