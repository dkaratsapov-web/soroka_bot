"""
Telegram-бот «лид-магнит за подписку» — гайд "10 проверенных маркетинговых стратегий".

Логика:
  1. /start -> если уже подписан, сразу отдаём материал; иначе показываем приветствие с кнопками.
  2. Кнопки приветствия: «Подписаться» (на канал) и «Я подписался».
  3. По «Я подписался» проверяем подписку через Telegram API (getChatMember).
  4. Подписан  -> отдаём текст с ссылкой на гайд.
     Не подписан -> сообщение «не вижу подписку» + кнопка «Проверить подписку снова».

Конфиг — из .env (см. .env.example). Бот должен быть АДМИНОМ канала.
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

# Картинка к первому сообщению (необязательно). Пусто -> сообщение без картинки.
# Это НЕ «барабан-заставка» до Start (та ставится в @BotFather), а фото в самом приветствии.
WELCOME_IMAGE = os.getenv("WELCOME_IMAGE", "").strip() or None

# Файл лид-магнита (необязательно). У нас гайд отдаётся ссылкой, поэтому по умолчанию пусто.
LEAD_MAGNET_FILE = os.getenv("LEAD_MAGNET_FILE", "").strip() or None

# ----------------------------- ТЕКСТЫ -----------------------------
WELCOME_TEXT = os.getenv(
    "WELCOME_TEXT",
    'Привет! 👋\n\n'
    'Для получения гайда «10 проверенных маркетинговых стратегий» подпишись на канал:',
)

LEAD_MAGNET_TEXT = os.getenv(
    "LEAD_MAGNET_TEXT",
    "✅ Спасибо за подписку!\n\n"
    "Вот твой эксклюзивный документ: clck.ru/3UJyuy\n"
    "Открывай и скачивай.\n\n"
    "Приятного изучения!",
)

NOT_SUBSCRIBED_TEXT = os.getenv(
    "NOT_SUBSCRIBED_TEXT",
    "Я пока не вижу подписку на канал. Подпишись и нажми кнопку ещё раз.",
)
# =========================================================================

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN не задан. Заполните .env (см. .env.example).")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


def welcome_keyboard() -> InlineKeyboardMarkup:
    """Кнопки приветствия: перейти в канал + проверить подписку."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подписаться", url=CHANNEL_URL)],
            [InlineKeyboardButton(text="Я подписался", callback_data="check_sub")],
        ]
    )


def recheck_keyboard() -> InlineKeyboardMarkup:
    """Кнопки на экране «подписку не вижу»."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подписаться", url=CHANNEL_URL)],
            [InlineKeyboardButton(text="Проверить подписку снова", callback_data="check_sub")],
        ]
    )


async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL, user_id=user_id)
        return member.status not in ("left", "kicked")
    except Exception as e:
        # Частая причина — бот не админ канала.
        logging.error("Ошибка проверки подписки: %s", e)
        return False


async def send_welcome(chat_id: int) -> None:
    kb = welcome_keyboard()
    if WELCOME_IMAGE:
        try:
            await bot.send_photo(
                chat_id=chat_id,
                photo=FSInputFile(WELCOME_IMAGE),
                caption=WELCOME_TEXT,
                reply_markup=kb,
            )
            return
        except Exception as e:
            logging.error("Не удалось отправить картинку, шлю текст: %s", e)
    await bot.send_message(chat_id=chat_id, text=WELCOME_TEXT, reply_markup=kb)


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
            logging.error("Не удалось отправить файл, шлю текст: %s", e)
    await bot.send_message(chat_id=chat_id, text=LEAD_MAGNET_TEXT)


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if await is_subscribed(message.from_user.id):
        await send_lead_magnet(message.chat.id)
    else:
        await send_welcome(message.chat.id)


@dp.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery) -> None:
    if await is_subscribed(callback.from_user.id):
        await callback.answer("Подписка найдена ✅")
        try:
            await callback.message.delete()
        except Exception:
            pass
        await send_lead_magnet(callback.message.chat.id)
    else:
        await callback.answer()  # закрываем «часики» на кнопке
        # Показываем экран «подписку не вижу» с кнопкой повторной проверки.
        try:
            await callback.message.edit_text(NOT_SUBSCRIBED_TEXT, reply_markup=recheck_keyboard())
        except Exception:
            # Если исходное сообщение было с картинкой (caption) — просто шлём новое.
            await callback.message.answer(NOT_SUBSCRIBED_TEXT, reply_markup=recheck_keyboard())


async def main() -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
