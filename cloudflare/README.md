# Бот на Cloudflare Workers (webhook)

Вариант запуска Telegram-бота без сервера. Подходит, когда хостинг не видит Telegram
(например, РФ-VPS с тротлингом): сеть Cloudflare достучится до Telegram сама.

Логика та же, что в Python-версии: `/start` → проверка подписки (`getChatMember`) →
выдача материала; кнопка «Я подписался ✅» перепроверяет.

## Деплой через панель Cloudflare (без командной строки)

1. Зарегистрируйся/войди на https://dash.cloudflare.com → раздел **Workers & Pages**.
2. **Create application** → **Create Worker** → дай имя (например `leadmagnet-bot`) → **Deploy**.
3. Открой созданный Worker → **Edit code** → удали шаблон, вставь содержимое `worker.js` → **Deploy**.
4. Открой **Settings → Variables and Secrets** и добавь:
   - `BOT_TOKEN` — тип **Secret** — токен от @BotFather
   - `WEBHOOK_SECRET` — тип **Secret** — любая длинная строка (защита webhook)
   - `CHANNEL` — `@sorokavmarketinge`
   - `CHANNEL_URL` — `https://t.me/sorokavmarketinge`
   - `LEAD_MAGNET_TEXT` — текст с материалом (например: `Спасибо за подписку! 🎉 Вот документ: clck.ru/3UJyuy`)
   - (необязательно) `WELCOME_TEXT`, `NOT_SUBSCRIBED_TEXT`
   Сохрани и снова **Deploy**.
5. Привяжи webhook: открой в браузере **один раз**
   `https://<имя-worker>.<твой-субдомен>.workers.dev/setup`
   — должно вернуться `{"ok":true, ...}`.
6. Сделай бота **администратором** канала `@sorokavmarketinge` (иначе проверка подписки не работает).

## Проверка
- С аккаунта **без** подписки: `/start` → бот предлагает подписаться, материал НЕ присылает.
- Подписаться → «Я подписался ✅» → приходит материал.

## Деплой через Wrangler CLI (альтернатива)
См. комментарии в `wrangler.toml`.

## Полезное
- Снять/посмотреть webhook: `https://api.telegram.org/bot<ТОКЕН>/getWebhookInfo`
- Логи Worker: в панели Cloudflare → Worker → **Logs** (Real-time).
