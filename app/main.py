import logging
from fastapi import FastAPI, Request
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
    allow_origins=["http://thekevindit.zapto.org", "https://web.postman.co"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# Подключаем роутер, указываем префикс и тег (опционально)
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])

@app.exception_handler(Exception)
async def server_error_handler(request: Request, exc: Exception):
    logger.error(f"Ошибка сервера: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Внутренняя ошибка сервера."},
    )
