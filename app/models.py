from sqlalchemy import Column, String, Boolean, DateTime
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, default=None)
    id_directus = Column(String, unique=True, nullable=False)
