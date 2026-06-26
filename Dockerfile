# Образ для запуска Telegram-бота «лид-магнит за подписку».
# Подходит для автодеплоя на Timeweb Cloud, Amvera и любой Docker-хостинг.
FROM python:3.12-slim

# Логи сразу в stdout (видны в панели хостинга), без .pyc-мусора.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Сначала зависимости — кешируется отдельным слоем, пересборка быстрее.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Затем код и картинка приветствия (welcome.jpg).
COPY . .

# Бот работает на long-polling, HTTP-порт не нужен — это фоновый worker.
CMD ["python", "leadmagnet_bot.py"]
