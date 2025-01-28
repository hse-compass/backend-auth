from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
import requests
import logging

from ..database import SessionLocal, Base
from ..models import User
from ..schemas import UserCreate, UserLogin
from ..security import verify_password, get_password_hash, create_access_token
from ..config import DIRECTUS_API_URL, DIRECTUS_ADMIN_TOKEN
from ..database import SessionLocal

logger = logging.getLogger(__name__)
router = APIRouter()


# Зависимость получения DB-сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email уже существует.")

    # Регистрируем пользователя в Directus
    response = requests.post(
        f"{DIRECTUS_API_URL}/users",
        headers={"Authorization": f"Bearer {DIRECTUS_ADMIN_TOKEN}"},
        json={
            "email": user_data.email,
            "password": user_data.password,
            "role": "55a9bff6-4e25-44c2-ba96-12be86f79d31"
        }
    )

    if response.status_code == 400:
        raise HTTPException(status_code=400, detail="Неверный формат email или пароля.")
    elif response.status_code == 500:
        raise HTTPException(status_code=500, detail="Ошибка на стороне Directus.")
    elif response.status_code != 200:
        logger.error(f"Unexpected Directus response: {response.status_code}, {response.json()}")
        raise HTTPException(status_code=500, detail="Ошибка регистрации в Directus.")

    directus_data = response.json()
    id_directus = directus_data.get("data", {}).get("id")
    if not id_directus:
        raise HTTPException(status_code=500, detail="Ошибка получения ID Directus.")

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        id=str(uuid4()),
        email=user_data.email,
        password_hash=hashed_password,
        id_directus=id_directus,
        last_login=None
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(data={"sub": user_data.email})
    return {"status": "success", "token": token}


@router.post("/login")
def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.login).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email не найден.")

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный пароль.")

    user.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token(data={"sub": user.email})
    return {"token": token}
