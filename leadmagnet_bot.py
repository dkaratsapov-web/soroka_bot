"""
Telegram-бот «лид-магнит за подписку».

Логика:
  1. /start -> если уже подписан, сразу отдаём материал; иначе показываем кнопки.
  2. Кнопки: «Подписаться на канал» и «Я подписался ✅».
  3. По «Я подписался» проверяем подписку через Telegram API (getChatMember).
  4. Подписан -> отдаём лид-магнит (файл и/или текст). Нет -> просим подписаться.

Конфиг берётся из .env (см. .env.example). Бот должен быть АДМИНОМ канала.
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from dotenv import load_dotenv

load_dotenv()

# ============================ CONFIG (из .env) ============================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL = os.getenv("CHANNEL", "@sorokavmarketinge")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/sorokavmarketinge")

# Путь к файлу лид-магнита (необязательно). Пусто -> уйдёт только текст.
LEAD_MAGNET_FILE = os.getenv("LEAD_MAGNET_FILE", "").strip() or None
LEAD_MAGNET_TEXT = os.getenv(
    "LEAD_MAGNET_TEXT",
    "Спасибо за подписку! 🎉\n\nВот ваш материал: https://example.com/your-link",
)

WELCOME_TEXT = os.getenv(
    "WELCOME_TEXT",
    "Привет! 👋\n\nЧтобы получить бесплатный материал, подпишитесь на канал "
    "и нажмите «Я подписался».",
)
NOT_SUBSCRIBED_TEXT = os.getenv(
    "NOT_SUBSCRIBED_TEXT",
    "Кажется, подписки пока нет 🤔\nПодпишитесь и нажмите «Я подписался ✅» ещё раз.",
)
# =========================================================================

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN не задан. Заполните .env (см. .env.example).")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


def subscribe_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться на канал", url=CHANNEL_URL)],
            [InlineKeyboardButton(text="Я подписался ✅", callback_data="check_sub")],
        ]
    )


async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL, user_id=user_id)
        return member.status not in ("left", "kicked")
    except Exception as e:
        # Самая частая причина — бот не админ канала.
        logging.error("Ошибка проверки подписки: %s", e)
        return False


async def send_lead_magnet(chat_id: int) -> None:
    if LEAD_MAGNET_FILE:
        try:
            await bot.send_document(
                chat_id=chat_id,
                document=FSInputFile(LEAD_MAGNET_FILE),
                caption=LEAD_MAGNET_TEXT,
            )
            return
        except Exception as e:
            logging.error("Не удалось отправить файл, шлю только текст: %s", e)
    await bot.send_message(chat_id=chat_id, text=LEAD_MAGNET_TEXT)


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if await is_subscribed(message.from_user.id):
        await send_lead_magnet(message.chat.id)
    else:
        await message.answer(WELCOME_TEXT, reply_markup=subscribe_keyboard())


@dp.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery) -> None:
    if await is_subscribed(callback.from_user.id):
        await callback.message.delete()
        await send_lead_magnet(callback.message.chat.id)
        await callback.answer()
    else:
        await callback.answer(NOT_SUBSCRIBED_TEXT, show_alert=True)


async def main() -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
