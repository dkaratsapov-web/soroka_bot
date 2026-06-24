# Деплой бота (запуск 24/7)

Бот должен работать там, где есть доступ к Telegram (`api.telegram.org`).
Секреты (`BOT_TOKEN` и т.д.) живут в `.env` на хосте и **в git не коммитятся**.

Два готовых варианта — выберите один.

## Вариант A. Docker (проще всего, подходит для любого VPS/ПК)

Нужен установленный Docker с плагином Compose.

```bash
cp .env.example .env      # затем заполните BOT_TOKEN, CHANNEL, CHANNEL_URL, текст материала
docker compose up -d --build
docker compose logs -f    # смотреть логи
docker compose down       # остановить
```

`restart: unless-stopped` — контейнер сам поднимется после перезагрузки сервера
или падения процесса.

Если выдаёте файл-лид-магнит: положите его в проект (например `materials/guide.pdf`),
раскомментируйте строку `COPY materials/` в `Dockerfile`, а в `.env` укажите
`LEAD_MAGNET_FILE=materials/guide.pdf`.

## Вариант B. VPS + systemd (без Docker)

```bash
# на сервере, например в /opt/leadmagnet-bot
git clone <repo> /opt/leadmagnet-bot
cd /opt/leadmagnet-bot
bash setup.sh             # venv + зависимости + .env из шаблона
nano .env                 # заполнить токен/канал/материал

sudo cp deploy/leadmagnet-bot.service /etc/systemd/system/
# при необходимости поправьте в unit-файле User и пути
sudo systemctl daemon-reload
sudo systemctl enable --now leadmagnet-bot

journalctl -u leadmagnet-bot -f      # логи
sudo systemctl restart leadmagnet-bot
```

`Restart=always` — бот перезапустится сам при сбое и после ребута сервера.

## Перед запуском в обоих вариантах
1. Бот должен быть **администратором** канала, иначе проверка подписки (`getChatMember`) не работает.
2. Проверьте end-to-end: неподписанному материал не уходит, подписанному — уходит.
3. Если токен светился в открытом виде — перевыпустите его в @BotFather (`/revoke`).
