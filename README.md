# Authentication Service
API для регистрации и авторизации пользователей.

## Установка

1. Клонируйте репозиторий:
    
2. Создайте виртуальное окружение и активируйте его:
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Установите зависимости:
    ```sh
    pip install -r requirements.txt
    ```

4. Настройте базу данных PostgreSQL и обновите переменную `DATABASE_URL` в файле `main.py`:
    ```python
    DATABASE_URL = "postgresql://<username>:<password>@localhost:5432/<database>"
    ```

## Запуск приложения

1. Запустите приложение с помощью Uvicorn:
    ```sh
    uvicorn app.main:app --reload
    ```

2. Приложение будет доступно по адресу `http://127.0.0.1:8000`.

## Использование API

### Регистрация пользователя

- **URL**: `/register`
- **Метод**: `POST`
- **Параметры запроса**:
    - `email`: Email пользователя
    - `password`: Пароль пользователя
- **Пример запроса**:
    ```sh
    curl -X 'POST' \
      'http://127.0.0.1:8000/register?email=user@example.com&password=password123' \
      -H 'accept: application/json' \
      -d ''
    ```
- **Ответ**:
    ```json
    {
        "access_token": "<token>",
        "token_type": "bearer"
    }
    ```

### Авторизация пользователя

- **URL**: `/login`
- **Метод**: `POST`
- **Параметры запроса**:
    - `email`: Email пользователя
    - `password`: Пароль пользователя
- **Пример запроса**:
    ```sh
    curl -X 'POST' \
      'http://127.0.0.1:8000/login?email=user@example.com&password=password123' \
      -H 'accept: application/json' \
      -d ''
    ```
- **Ответ**:
    ```json
    {
        "access_token": "<token>",
        "token_type": "bearer"
    }
    ```
## Тестирование

1. Создайте тестовую базу данных PostgreSQL и обновите переменную `DATABASE_URL` в файле `test.py`:
    ```python
    DATABASE_URL = "postgresql://<username>:<password>@localhost:5432/<test_database>"
    ```

2. Запустите тесты с помощью команды:
    ```sh
    python -m unittest test.py
    ```

## Зависимости

- FastAPI
- SQLAlchemy
- Uvicorn
- Passlib
- Python-Jose
- PostgreSQL

## Запрос для создания базы данных в PostgreSQL
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
    email VARCHAR(255) NOT NULL,                  
    password_hash VARCHAR(255) NOT NULL,          
    roles JSON NOT NULL DEFAULT '{"role": "user"}', 
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,  
    updated_at TIMESTAMP DEFAULT NOW(),           
    is_active BOOLEAN DEFAULT TRUE NOT NULL,      
    last_login TIMESTAMP,                         
    refresh_token TEXT,                           
    reset_password_token TEXT,                    
    reset_password_exp TIMESTAMP                  
);
```
