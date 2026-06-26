# Автодеплой на Cloudflare Workers (бесплатно)

Бот переписан на JavaScript (grammY) и работает на Cloudflare Workers через **webhook**.
Хостинг бесплатный (free-tier с запасом), доступен из РФ, карта для старта не нужна.

Схема: пуш в GitHub → GitHub Actions публикует воркер на Cloudflare → Telegram шлёт
обновления на адрес воркера. Картинка `welcome.jpg` отдаётся самим воркером (папка `public/`).

Файлы в репозитории:
- `src/index.js` — код бота (grammY + webhook).
- `wrangler.toml` — конфиг воркера (имя, статика).
- `package.json` — зависимости (`grammy`, `wrangler`).
- `public/welcome.jpg` — картинка приветствия.
- `.github/workflows/deploy.yml` — автодеплой.

---

## Что нужно от вас — разовая настройка (~15 минут)

### Шаг 1. Аккаунт Cloudflare
Зарегистрируйтесь на https://dash.cloudflare.com (бесплатно). Раздел **Workers & Pages**
при первом входе предложит выбрать ваш бесплатный сабдомен вида `<имя>.workers.dev` — выберите любой.

### Шаг 2. API-токен для GitHub
1. Cloudflare → **My Profile → API Tokens → Create Token**.
2. Шаблон **Edit Cloudflare Workers** → Continue → Create Token.
3. Скопируйте токен (показывается один раз). 👉 Это секрет **`CLOUDFLARE_API_TOKEN`**.

### Шаг 3. Account ID
На главной Workers & Pages справа найдите **Account ID** и скопируйте.
👉 Это секрет **`CLOUDFLARE_ACCOUNT_ID`**.

### Шаг 4. Придумайте WEBHOOK_SECRET
Любая случайная строка (буквы/цифры, 20–40 символов) — защищает webhook.
Например сгенерировать: на сайте или командой `openssl rand -hex 24`.
👉 Это секрет **`WEBHOOK_SECRET`**. Запомните — он ещё понадобится в шаге 6.

### Шаг 5. Секреты в GitHub
Репозиторий → **Settings → Secrets and variables → Actions → New repository secret**.
Добавьте четыре:

| Секрет | Значение |
|---|---|
| `CLOUDFLARE_API_TOKEN` | токен из шага 2 |
| `CLOUDFLARE_ACCOUNT_ID` | ID из шага 3 |
| `BOT_TOKEN` | токен бота от @BotFather |
| `WEBHOOK_SECRET` | строка из шага 4 |

> Токен бота и секрет хранятся только как секреты — в код/репозиторий не попадают.
> При деплое GitHub Actions сам загрузит их в воркер.

### Шаг 6. Первый деплой и регистрация webhook
1. Любой пуш в ветку (или вкладка **Actions → Deploy to Cloudflare Workers → Run workflow**)
   опубликует воркер. Зелёная галочка = успех.
2. Узнайте URL воркера: Cloudflare → Workers & Pages → `marketing-guide-bot` →
   адрес вида `https://marketing-guide-bot.<ваш-сабдомен>.workers.dev`.
3. **Один раз** откройте в браузере (подставьте свой WEBHOOK_SECRET):
   ```
   https://marketing-guide-bot.<ваш-сабдомен>.workers.dev/init?token=ВАШ_WEBHOOK_SECRET
   ```
   Должно ответить «Webhook установлен на ...». Это привязывает Telegram к воркеру.
   (Повторять нужно только если поменяется URL воркера.)

### Шаг 7. Сделать бота админом канала
В Telegram: канал `@sorokavmarketinge` → Администраторы → добавить вашего бота.
Без этого проверка подписки не работает.

---

## Проверка
Напишите боту `/start` — придёт приветствие с картинкой и кнопками. Нажмите «Я подписался»:
- подписаны → бот удалит приветствие и пришлёт ссылку на гайд;
- не подписаны → сообщение «не вижу подписку» с кнопкой повторной проверки.

Логи в реальном времени: Cloudflare → воркер → вкладка **Logs** (или `npx wrangler tail`).

---

## Дальше — полная автоматизация правок
Вы говорите, что поменять (текст, кнопку, логику) → я правлю `src/index.js`, коммичу и пушу
→ GitHub Actions публикует обновление на Cloudflare за ~1 минуту. Ручных действий с вашей
стороны после первичной настройки — ноль.

---

## Альтернатива без GitHub Actions (Workers Builds)
Можно вместо шагов 2–6 подключить репозиторий прямо в Cloudflare:
Workers & Pages → Create → Workers → **Connect to Git** → выбрать репозиторий.
Тогда Cloudflare сам собирает при каждом пуше. Секреты `BOT_TOKEN` и `WEBHOOK_SECRET`
в этом случае задаются в настройках воркера (Settings → Variables and Secrets),
а webhook регистрируется так же через `/init` (шаг 6.3).
