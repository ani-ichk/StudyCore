from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import List, Dict

import bcrypt

from server.data.db.models import User
from server.data.db.auth_methods import authenticate_user
from server.data.db.add_methods import add_user_with_roles
from server.data.db.read_methods import get_user_roles
from server.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from server.data.db.qr_service import QRCodeGenerator
from server.data.db.main import db_manager

router = APIRouter(prefix="/auth", tags=["Авторизация и пользователи"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

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

def _verify_legacy_bcrypt(password: str, hashed: str) -> bool:
    """Проверка старого формата хэша "bcrypt$<salt>$$<hash>"."""
    try:
        if not hashed.startswith("bcrypt$"):
            return False

        raw = hashed[len("bcrypt$"):]
        parts = raw.split("$$", 1)
        if len(parts) != 2:
            return False

        bcrypt_hash = parts[1]
        if not bcrypt_hash.startswith("$"):
            bcrypt_hash = "$" + bcrypt_hash
        return bcrypt.checkpw(password.encode("utf-8"), bcrypt_hash.encode("utf-8"))
    except Exception:
        return False


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        user = db.query(User).filter_by(login=form_data.username).first()
        if not user or not _verify_legacy_bcrypt(form_data.password, user.password):
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
