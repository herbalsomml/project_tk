# Используем официальный образ Python 3.11 (можете изменить на версию, которая вам нужна)
FROM python:3.11-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл requirements.txt в контейнер
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы вашего проекта в контейнер
COPY . .

# Команда для запуска бота
CMD ["python", "bot.py"]
