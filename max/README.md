# MAX-бот «лид-магнит за подписку»

Версия бота для мессенджера **MAX** (`platform-api.max.ru`) на библиотеке
[`maxapi`](https://github.com/max-messenger/max-botapi-python). Логика та же, что в
Telegram: `/start` → проверка подписки на канал (`get_chat_member`) → выдача материала;
кнопка «Я подписался ✅» перепроверяет.

Запускается на **Reg.ru VPS** — из РФ-сети MAX API доступен (в отличие от Telegram).
Режим — **long polling** (внешний IP/SSL не нужен). Для прода MAX рекомендует webhook
(см. ниже).

## Предварительно
1. Бот создан через **@MasterBot**, токен получен.
2. Бот **добавлен администратором** канала `https://max.ru/id773126457242_biz` —
   иначе проверка подписки не сработает.

## Деплой на VPS (Docker)

```bash
# на сервере, где уже стоит Docker
git clone -b main https://github.com/dkaratsapov-web/soroka_bot.git
cd soroka_bot/max
cp .env.example .env
nano .env            # вписать MAX_BOT_TOKEN (канал/тексты уже заполнены)

docker compose up -d --build
docker compose logs -f
```

В логах при старте бот:
- определит числовой ID канала из ссылки (`CHANNEL_ID из ссылки ... -> ...`);
- выведет список чатов, где он состоит (для диагностики).

Если ID канала не определился — добавьте бота админом канала и перезапустите,
либо задайте `MAX_CHANNEL_ID` вручную (число из лога «Чат бота: id=...»).

## Деплой на VPS (без Docker)

```bash
cd soroka_bot/max
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env
python max_bot.py
```

Для постоянной работы оформите systemd-сервис (по аналогии с
`deploy/leadmagnet-bot.service` в корне репозитория).

## Проверка
- С аккаунта **без подписки**: открыть бота / `/start` → бот предлагает подписаться,
  материал НЕ присылает.
- Подписаться на канал → «Я подписался ✅» → приходит материал.

## Прод: webhook (позже)
Long polling подходит для старта. Для продакшена в MAX используется webhook
(нужен домен + HTTPS на VPS). Библиотека `maxapi` поддерживает webhook
(`maxapi.webhook`, варианты под aiohttp/FastAPI/Litestar) — переведём при необходимости.

## Ограничения MAX
Публиковать бота можно только от **верифицированного юрлица/ИП — резидента РФ**;
модерация — до ~48 часов. См. https://dev.max.ru
