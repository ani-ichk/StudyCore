from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import List, Dict


from models import User
from auth_methods import authenticate_user
from add_methods import add_user_with_roles
from read_methods import get_user_roles
from security import PasswordHasher
from qr_service import QRCodeGenerator
from db_manager import DatabaseManager

router = APIRouter(prefix="/auth", tags=["Авторизация и пользователи"])

SECRET_KEY = "school-system-very-secret-key-2026-change-me-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

db_manager = DatabaseManager()

def get_db():
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недействительные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        roles: List[str] = payload.get("roles", [])
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).get(user_id)
    if not user:
        raise credentials_exception

    return {
        "id": user.id,
        "login": user.login,
        "full_name": f"{user.surname} {user.name} {user.patronymic or ''}".strip(),
        "roles": roles
    }

def require_roles(*required: str):
    """Проверка прав: есть ли хотя бы одна из требуемых ролей"""
    async def checker(current: Dict = Depends(get_current_user)):
        if not any(r in current["roles"] for r in required):
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        return current
    return checker

#эндпоинты

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(401, "Неверный логин или пароль")

    roles = [r.name for r in get_user_roles(db, user.id)]

    token = create_access_token({"sub": user.id, "roles": roles})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "roles": roles
    }

@router.post("/register")
def register(
    login: str,
    password: str,
    surname: str,
    name: str,
    role_names: List[str] = ["student"],
    patronymic: str | None = None,
    phone: str | None = None,
    db: Session = Depends(get_db)
):
    try:
        user = add_user_with_roles(
            session=db,
            login=login,
            password=password,
            surname=surname,
            name=name,
            role_names=role_names,
            patronymic=patronymic,
            phone=phone
        )
        return {"ok": True, "user_id": user.id, "roles": role_names}
    except Exception as e:
        raise HTTPException(400, f"Ошибка: {str(e)}")

@router.get("/me")
def me(current: Dict = Depends(get_current_user), db: Session = Depends(get_db)):
    qr_gen = QRCodeGenerator(db_manager)
    qr = qr_gen.generate_user_qr_code(current["id"], purpose="attendance")

    return {
        **current,
        "qr_code_base64": qr["image_base64"],
        "qr_expires_at": qr["expires_at"]
    }
