from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import Column, String, Boolean, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from uuid import uuid4
import os
from dotenv import load_dotenv
import requests
import logging

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
DIRECTUS_API_URL = os.getenv("DIRECTUS_API_URL")
DIRECTUS_ADMIN_TOKEN = os.getenv("DIRECTUS_ADMIN_TOKEN")

Base = declarative_base()
engine = create_engine(DATABASE_URL,
                       connect_args={'options': '-csearch_path=auth'})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, default=None)
    id_directus = Column(String, unique=True, nullable=False)  

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.exception_handler(Exception)
async def server_error_handler(request: Request, exc: Exception):
    logger.error(f"Ошибка сервера: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Внутренняя ошибка сервера."},
    )

@app.post("/api/v1/users/register", status_code=200)
def register_user(email: str, password: str, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email уже существует.")

        response = requests.post(
            f"{DIRECTUS_API_URL}/users",
            headers={"Authorization": f"Bearer {DIRECTUS_ADMIN_TOKEN}"},
            json={"email": email, "password": password, "role": "55a9bff6-4e25-44c2-ba96-12be86f79d31"}
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

        hashed_password = get_password_hash(password)
        new_user = User(
            id=str(uuid4()),
            email=email,
            password_hash=hashed_password,
            id_directus=id_directus,
            last_login=None
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = create_access_token(data={"sub": email})
        return {"status": "success", "token": token}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя API: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


@app.post("/api/v1/users/login", status_code=200)
def login_user(login: str, password: str, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == login).first()
        if not user:
            raise HTTPException(status_code=404, detail="Email не найден.")

        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=400, detail="Неверный пароль.")

        user.last_login = datetime.utcnow()
        db.commit()

        token = create_access_token(data={"sub": user.email})
        return {"token": token}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Ошибка при авторизации пользователя: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")
