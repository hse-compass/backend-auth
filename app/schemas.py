from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    login: EmailStr
    password: str

class UserResponse(BaseModel):
    email: EmailStr
    last_login: Optional[datetime] = None

    class Config:
        orm_mode = True
