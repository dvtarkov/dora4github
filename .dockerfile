# Устанавливаем базовый образ. Выберем образ Python 3.
FROM python:3.9-slim

# Устанавливаем рабочий каталог в контейнере
WORKDIR /app

# Копируем файл зависимостей в рабочий каталог
COPY requirements.txt /app/

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы приложения в рабочий каталог
COPY . /app

# Объявляем порт, на котором будет работать приложение
EXPOSE 5000

# Задаем переменные окружения для Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Команда для запуска приложения
CMD ["flask", "--app", "github-dora-metrics.py", "run"]