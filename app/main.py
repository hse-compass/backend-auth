import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем таблицы, если их нет
Base.metadata.create_all(bind=engine)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://thekevindit.zapto.org", 
        "https://web.postman.co", 
        "http://thekevindit.zapto.org:3000",
        "http://thekevindit.zapto.org:8055",
        "http://localhost:3000",
        "http://localhost",
        "http://127.0.0.1"
    ],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# Подключаем роутер, указываем префикс и тег (опционально)
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
