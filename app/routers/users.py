from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
import requests
import logging
from fastapi.responses import JSONResponse
from fastapi import Request
from jose import jwt

from ..database import SessionLocal, Base
from ..models import User
from ..schemas import UserCreate, UserLogin, TokenData
from ..security import verify_password, get_password_hash, create_access_token, create_refresh_token
from ..config import DIRECTUS_API_URL, DIRECTUS_ADMIN_TOKEN, ALGORITHM, REFRESH_SECRET_KEY, SECRET_KEY
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
        f"{DIRECTUS_API_URL}/users/register",
        json={
            "email": user_data.email,
            "password": user_data.password,
        }
    )

    if response.status_code == 400:
        raise HTTPException(status_code=400, detail="Неверный формат email или пароля.")
    elif response.status_code == 500:
        raise HTTPException(status_code=500, detail="Ошибка на стороне Directus.")
    elif response.status_code not in {200, 201, 204}:  # Обрабатываем возможные коды успеха
        try:
            error_details = response.json()
        except requests.exceptions.JSONDecodeError:
            error_details = "Invalid response from Directus"
        logger.error(f"Unexpected Directus response: {response.status_code}, {error_details}")
        raise HTTPException(status_code=500, detail="Ошибка регистрации в Directus.")

    response = requests.get(
        f"{DIRECTUS_API_URL}/users?filter[email][_eq]={user_data.email}",
        headers={"Authorization": f"Bearer {DIRECTUS_ADMIN_TOKEN}"},
    )

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Ошибка получения данных пользователя из Directus.")

    directus_data = response.json()
    users_list = directus_data.get("data", [])
    if not users_list:
        raise HTTPException(status_code=500, detail="Ошибка получения ID Directus.")

    id_directus = users_list[0].get("id")

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
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email не найден.")

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный пароль.")

    response = requests.get(
        f"{DIRECTUS_API_URL}/users?filter[email][_eq]={user_data.email}",
        headers={"Authorization": f"Bearer {DIRECTUS_ADMIN_TOKEN}"},
    )

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Ошибка получения данных пользователя из Directus.")

    directus_data = response.json()
    users_list = directus_data.get("data", [])
    if not users_list:
        raise HTTPException(status_code=500, detail="Ошибка получения ID Directus.")

    status = users_list[0].get("status")

    if status == "unverified":
        raise HTTPException(status_code=401, detail="Пользователь не подтвержден")

    user.last_login = datetime.utcnow()
    db.commit()

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    response = JSONResponse(content={
        "access_token": access_token
    })

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="strict",
        max_age=60 * 60 * 24 * 7
    )

    return response


@router.post("/refresh")
def refresh_token(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found")

    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Refresh token is invalid")

    new_access_token = create_access_token(data={"sub": payload["sub"]})

    return {"access_token": new_access_token}


@router.post("/logout")
def logout():
    response = JSONResponse(content={"status": "ok"})
    response.delete_cookie("refresh_token")
    return response


@router.get("/me")
def get_me(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    access_token = parts[1]

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token is invalid or expired")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "email": user.email,
        "id": user.id,
        "directus_id": user.id_directus,
    }
