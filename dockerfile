# Используем официальный Python образ
FROM --platform=linux/amd64 python:3.10-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . /app/

# Обновляем pip
RUN pip install --upgrade pip

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Открываем порт для приложения (по умолчанию FastAPI работает на порту 8000)
EXPOSE 8000

# Запускаем приложение с помощью Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
