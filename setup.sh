#!/usr/bin/env bash
# Первичная настройка проекта: venv + зависимости + .env
# Запуск:  bash setup.sh
set -e

echo "==> Проверяю Python..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 не найден. Установите Python 3.10+ и повторите."
  exit 1
fi
python3 --version

echo "==> Создаю виртуальное окружение (venv)..."
python3 -m venv venv

echo "==> Ставлю зависимости..."
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt

if [ ! -f .env ]; then
  echo "==> Создаю .env из шаблона..."
  cp .env.example .env
  echo "    Готово. Откройте .env и заполните BOT_TOKEN, CHANNEL, CHANNEL_URL и текст материала."
else
  echo "==> .env уже существует, не трогаю."
fi

echo ""
echo "============================================"
echo "Настройка завершена."
echo "Дальше:"
echo "  1) Заполните .env (токен от @BotFather, канал, текст/файл материала)."
echo "  2) Сделайте бота АДМИНИСТРАТОРОМ канала."
echo "  3) Запуск:  source venv/bin/activate && python leadmagnet_bot.py"
echo "============================================"
