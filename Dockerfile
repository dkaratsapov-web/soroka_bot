# Образ для бота «лид-магнит за подписку».
# Конфиг (BOT_TOKEN и т.д.) передаётся через переменные окружения / .env,
# внутрь образа секреты НЕ зашиваются.
FROM python:3.12-slim

# Не писать .pyc, не буферизовать stdout (логи видны сразу).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Сначала зависимости — лучше кешируется при пересборке.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Затем код бота.
COPY leadmagnet_bot.py .

# Если используете файл-лид-магнит, положите его рядом и укажите путь
# в LEAD_MAGNET_FILE (например ./materials/guide.pdf) — он скопируется строкой ниже.
# COPY materials/ ./materials/

CMD ["python", "leadmagnet_bot.py"]
