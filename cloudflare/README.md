# Бот на Cloudflare Workers (webhook) — авто-деплой из GitHub

Запуск Telegram-бота без сервера. Подходит, когда хостинг не видит Telegram
(РФ-VPS с тротлингом): сеть Cloudflare достучится до Telegram сама.
При каждом `git push` Cloudflare пересобирает и публикует воркер автоматически.

Логика та же, что в Python-версии: `/start` → проверка подписки (`getChatMember`) →
выдача материала; кнопка «Я подписался ✅» перепроверяет.

Файлы:
- `cloudflare/worker.js` — код воркера.
- `wrangler.toml` (в корне репозитория) — имя воркера, точка входа, несекретные переменные.

## Деплой из GitHub (автоматический)

1. https://dash.cloudflare.com → **Workers & Pages** → **Create** → **Import a repository**.
2. Подключи GitHub и выбери репозиторий `soroka_bot`.
3. Настройки сборки:
   - **Build command** — оставить пустым;
   - **Deploy command** — `npx wrangler deploy`;
   - **Production branch** — ветка, где лежит код (`main`).
4. **Deploy**. Cloudflare прочитает корневой `wrangler.toml` и опубликует воркер.
5. **Settings → Variables and Secrets** — добавь секреты (в git их нет):
   - `BOT_TOKEN` — тип **Secret** — токен от @BotFather;
   - `WEBHOOK_SECRET` — тип **Secret** — любая длинная строка.
   Несекретные `CHANNEL`, `CHANNEL_URL`, `LEAD_MAGNET_TEXT` уже заданы в `wrangler.toml`.
6. Нажми **Retry deployment** (или сделай пустой commit), чтобы секреты применились.
7. Привяжи webhook — открой один раз в браузере:
   `https://leadmagnet-bot.<твой-субдомен>.workers.dev/setup` → ждём `{"ok":true,...}`.
8. Сделай бота **администратором** канала `@sorokavmarketinge`.

После этого каждый `git push` в ветку деплоя обновляет бота сам.

## Проверка
- С аккаунта **без** подписки: `/start` → бот предлагает подписаться, материал НЕ присылает.
- Подписаться → «Я подписался ✅» → приходит материал.

## Полезное
- Статус webhook: `https://api.telegram.org/bot<ТОКЕН>/getWebhookInfo`
- Логи воркера: панель Cloudflare → Worker → **Logs** (Real-time).
