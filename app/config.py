import os

SECRET_KEY = os.getenv("SECRET_KEY", "secret")  # лучше поднять ошибку, если SECRET_KEY не задан
DATABASE_URL = os.getenv("DATABASE_URL")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
DIRECTUS_API_URL = os.getenv("DIRECTUS_API_URL", "")
DIRECTUS_ADMIN_TOKEN = os.getenv("DIRECTUS_ADMIN_TOKEN", "")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "")
