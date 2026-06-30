"""
MAX-бот «лид-магнит за подписку» (мессенджер MAX, platform-api.max.ru).

Логика повторяет Telegram-версию:
  - старт бота / команда /start -> если подписан на канал, сразу отдаём материал;
    иначе показываем кнопки «Подписаться на канал» и «Я подписался ✅».
  - кнопка «Я подписался» -> перепроверяем членство (get_chat_member) и выдаём материал.

Библиотека: maxapi (https://github.com/max-messenger/max-botapi-python).
Конфиг — из .env (см. .env.example). Бот должен быть АДМИНОМ канала, иначе
проверка подписки не работает.

Запуск: long polling. Для прода MAX рекомендует webhook — см. README.md.
"""

import asyncio
import logging
import os

from dotenv import load_dotenv

from maxapi import Bot, Dispatcher
from maxapi.enums.upload_type import UploadType
from maxapi.types import (
    BotAdded,
    BotStarted,
    Command,
    InputMedia,
    MessageCallback,
    MessageCreated,
)
from maxapi.types.attachments.buttons import CallbackButton, LinkButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

load_dotenv()

# ============================ CONFIG (из .env) ============================
MAX_BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")

# Канал для подписки. Ссылка идёт на кнопку «Подписаться» и используется для
# определения числового ID канала (если MAX_CHANNEL_ID не задан явно).
MAX_CHANNEL_LINK = os.getenv("MAX_CHANNEL_LINK", "https://max.ru/id773126457242_biz")
# Необязательно: числовой ID канала. Если пусто — определим из ссылки при старте.
MAX_CHANNEL_ID = os.getenv("MAX_CHANNEL_ID", "").strip()

LEAD_MAGNET_TEXT = os.getenv(
    "MAX_LEAD_MAGNET_TEXT",
    "Спасибо за подписку! 🎉 Держи гайд «10 проверенных маркетинговых стратегий» — "
    "файл ниже 👇 Приятного изучения!",
)
# Путь к файлу-лид-магниту внутри контейнера. Пусто -> уйдёт только текст.
LEAD_MAGNET_FILE = (
    os.getenv("MAX_LEAD_MAGNET_FILE", "marketing-guide-2026.pdf").strip() or None
)
WELCOME_TEXT = os.getenv(
    "MAX_WELCOME_TEXT",
    'Привет! 👋\n\nДля получения гайда "10 проверенных маркетинговых стратегий" '
    'подпишись на канал "Сорокин в Маркетинге"',
)
NOT_SUBSCRIBED_TEXT = os.getenv(
    "MAX_NOT_SUBSCRIBED_TEXT",
    "Кажется, подписки пока нет 🤔 Подпишись на канал и нажми «Я подписался ✅» ещё раз.",
)
# =========================================================================

logging.basicConfig(level=logging.INFO)

if not MAX_BOT_TOKEN:
    raise SystemExit("MAX_BOT_TOKEN не задан. Заполните .env (см. .env.example).")

bot = Bot(MAX_BOT_TOKEN)
dp = Dispatcher()

# Числовой ID канала — резолвится при старте (см. resolve_channel_id).
channel_id: int | None = int(MAX_CHANNEL_ID) if MAX_CHANNEL_ID else None


def subscribe_keyboard():
    kb = InlineKeyboardBuilder()
    kb.row(LinkButton(text="📢 Подписаться на канал", url=MAX_CHANNEL_LINK))
    kb.row(CallbackButton(text="Я подписался ✅", payload="check_sub"))
    return kb.as_markup()


async def is_subscribed(user_id: int) -> bool:
    if channel_id is None:
        logging.error("channel_id не определён — проверка подписки невозможна.")
        return False
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member is not None
    except Exception as e:
        # Частая причина — бот не админ канала.
        logging.error("Ошибка проверки подписки: %s", e)
        return False


async def send_lead_magnet(chat_id: int) -> None:
    if LEAD_MAGNET_FILE:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=LEAD_MAGNET_TEXT,
                attachments=[InputMedia(path=LEAD_MAGNET_FILE, type=UploadType.FILE)],
            )
            return
        except Exception as e:
            logging.error("Не удалось отправить файл, шлю только текст: %s", e)
    await bot.send_message(chat_id=chat_id, text=LEAD_MAGNET_TEXT)


async def offer_subscription(chat_id: int) -> None:
    await bot.send_message(
        chat_id=chat_id, text=WELCOME_TEXT, attachments=[subscribe_keyboard()]
    )


async def handle_entry(chat_id, user_id) -> None:
    if chat_id is None or user_id is None:
        return
    if await is_subscribed(user_id):
        await send_lead_magnet(chat_id)
    else:
        await offer_subscription(chat_id)


@dp.bot_started()
async def on_bot_started(event: BotStarted) -> None:
    chat_id, user_id = event.get_ids()
    await handle_entry(chat_id, user_id)


@dp.message_created(Command("start"))
async def on_start(event: MessageCreated) -> None:
    chat_id, user_id = event.get_ids()
    await handle_entry(chat_id, user_id)


@dp.message_callback()
async def on_callback(event: MessageCallback) -> None:
    if event.callback.payload != "check_sub":
        return
    chat_id, user_id = event.get_ids()
    if await is_subscribed(user_id):
        # MAX требует, чтобы в ответе на callback был message или notification.
        await bot.send_callback(
            callback_id=event.callback.callback_id,
            notification="Спасибо за подписку! Отправляю материал 👇",
        )
        if chat_id is not None:
            await send_lead_magnet(chat_id)
        else:
            await bot.send_message(user_id=user_id, text=LEAD_MAGNET_TEXT)
    else:
        await bot.send_callback(
            callback_id=event.callback.callback_id,
            notification=NOT_SUBSCRIBED_TEXT,
        )


@dp.bot_added()
async def on_bot_added(event: BotAdded) -> None:
    """Когда бота добавляют в канал/чат — печатаем chat_id и подхватываем его."""
    global channel_id
    kind = "канал" if event.is_channel else "чат"
    logging.info(
        "➡️  Бота добавили в %s. chat_id=%s. Если это нужный канал — впишите в .env "
        "строку MAX_CHANNEL_ID=%s и перезапустите (чтобы сохранилось после рестарта).",
        kind,
        event.chat_id,
        event.chat_id,
    )
    if channel_id is None and event.is_channel:
        channel_id = event.chat_id
        logging.info(
            "CHANNEL_ID подхвачен автоматически из события добавления: %s", channel_id
        )


async def resolve_channel_id() -> None:
    """Определяет числовой ID канала из ссылки (если не задан явно)."""
    global channel_id
    if channel_id is not None:
        logging.info("CHANNEL_ID задан явно: %s", channel_id)
        return
    try:
        chat = await bot.get_chat_by_link(MAX_CHANNEL_LINK)
        channel_id = chat.chat_id
        logging.info("CHANNEL_ID из ссылки %s -> %s", MAX_CHANNEL_LINK, channel_id)
    except Exception as e:
        logging.warning(
            "ID канала по ссылке %s пока не получен (%s). Это нормально, если бот ещё "
            "не добавлен в канал — добавьте его администратором, и chat_id определится.",
            MAX_CHANNEL_LINK,
            e,
        )


async def main() -> None:
    await bot.delete_webhook()
    await resolve_channel_id()
    if channel_id is None:
        logging.warning(
            "CHANNEL_ID пока не определён. Добавьте бота АДМИНИСТРАТОРОМ в канал %s — "
            "бот поймает событие и напечатает chat_id (впишите его в MAX_CHANNEL_ID).",
            MAX_CHANNEL_LINK,
        )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
