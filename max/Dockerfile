# Образ MAX-бота. Секреты передаются через .env, в образ не зашиваются.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY max_bot.py .

CMD ["python", "max_bot.py"]
