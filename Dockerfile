FROM python:3.13-slim

WORKDIR /app

# Обновляем систему и устанавливаем необходимые системные пакеты
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем все зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Запуск приложения
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "page_analyzer:app"]