/**
 * Telegram-бот «лид-магнит за подписку» на Cloudflare Workers (grammY + webhook).
 *
 * Логика повторяет Python-версию (leadmagnet_bot.py):
 *   1. /start -> подписан? сразу гайд : приветствие с кнопками.
 *   2. Кнопки: «Подписаться» (на канал) и «Я подписался».
 *   3. По «Я подписался» проверяем подписку через getChatMember.
 *   4. Подписан -> текст с ссылкой на гайд; не подписан -> «не вижу подписку» + кнопка.
 *
 * Картинку welcome.jpg отдаёт сам воркер из папки public/ (Cloudflare Static Assets),
 * а Telegram забирает её по публичному URL воркера.
 *
 * Секреты (задаются как переменные окружения воркера, НЕ в коде):
 *   BOT_TOKEN      — токен от @BotFather
 *   WEBHOOK_SECRET — произвольная строка; защищает webhook и эндпоинт /init
 */

import { Bot, InlineKeyboard, webhookCallback } from "grammy";

// ----------------------------- КОНФИГ -----------------------------
const CHANNEL = "@karatsapov_test";
const CHANNEL_URL = "https://t.me/karatsapov_test";

// ----------------------------- ТЕКСТЫ (по ТЗ) -----------------------------
const WELCOME_TEXT =
  "Привет! 👋\n\n" +
  "Для получения гайда «10 проверенных маркетинговых стратегий» подпишись на канал:";

const LEAD_MAGNET_TEXT =
  "✅ Спасибо за подписку!\n\n" +
  "Вот твой эксклюзивный документ: clck.ru/3UJyuy\n" +
  "Открывай и скачивай.\n\n" +
  "Приятного изучения!";

const NOT_SUBSCRIBED_TEXT =
  "Я пока не вижу подписку на канал. Подпишись и нажми кнопку ещё раз.";

// ----------------------------- КЛАВИАТУРЫ -----------------------------
function welcomeKeyboard() {
  return new InlineKeyboard()
    .url("Подписаться", CHANNEL_URL)
    .row()
    .text("Я подписался", "check_sub");
}

function recheckKeyboard() {
  return new InlineKeyboard()
    .url("Подписаться", CHANNEL_URL)
    .row()
    .text("Проверить подписку снова", "check_sub");
}

// ----------------------------- ЛОГИКА -----------------------------
async function isSubscribed(bot, userId) {
  try {
    const member = await bot.api.getChatMember(CHANNEL, userId);
    return !["left", "kicked"].includes(member.status);
  } catch (e) {
    // Частая причина — бот не админ канала.
    console.error("Ошибка проверки подписки:", e);
    return false;
  }
}

/** Собираем бота на каждый запрос (так устроены Workers). photoUrl — абсолютный URL картинки. */
function createBot(env, photoUrl) {
  const bot = new Bot(env.BOT_TOKEN);

  async function sendWelcome(ctx) {
    if (photoUrl) {
      try {
        await ctx.replyWithPhoto(photoUrl, {
          caption: WELCOME_TEXT,
          reply_markup: welcomeKeyboard(),
        });
        return;
      } catch (e) {
        console.error("Не удалось отправить картинку, шлю текст:", e);
      }
    }
    await ctx.reply(WELCOME_TEXT, { reply_markup: welcomeKeyboard() });
  }

  async function sendLeadMagnet(ctx) {
    await ctx.reply(LEAD_MAGNET_TEXT);
  }

  bot.command("start", async (ctx) => {
    if (await isSubscribed(bot, ctx.from.id)) {
      await sendLeadMagnet(ctx);
    } else {
      await sendWelcome(ctx);
    }
  });

  bot.callbackQuery("check_sub", async (ctx) => {
    if (await isSubscribed(bot, ctx.from.id)) {
      await ctx.answerCallbackQuery("Подписка найдена ✅");
      try {
        await ctx.deleteMessage();
      } catch (_) {
        /* сообщение могло быть уже удалено */
      }
      await sendLeadMagnet(ctx);
    } else {
      await ctx.answerCallbackQuery(); // закрываем «часики» на кнопке
      try {
        // Если исходное сообщение было текстовым — редактируем его.
        await ctx.editMessageText(NOT_SUBSCRIBED_TEXT, {
          reply_markup: recheckKeyboard(),
        });
      } catch (_) {
        // Если было с картинкой (caption) — текст не отредактировать, шлём новое.
        await ctx.reply(NOT_SUBSCRIBED_TEXT, { reply_markup: recheckKeyboard() });
      }
    }
  });

  return bot;
}

// ----------------------------- HTTP / WEBHOOK -----------------------------
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Разовая регистрация webhook: открыть в браузере /init?token=WEBHOOK_SECRET
    if (url.pathname === "/init") {
      if (url.searchParams.get("token") !== env.WEBHOOK_SECRET) {
        return new Response("forbidden", { status: 403 });
      }
      const bot = createBot(env);
      const webhookUrl = `${url.origin}/`;
      await bot.api.setWebhook(webhookUrl, {
        secret_token: env.WEBHOOK_SECRET,
        drop_pending_updates: true,
      });
      return new Response(`Webhook установлен на ${webhookUrl}`);
    }

    // Входящие апдейты от Telegram (POST). Картинка отдаётся по нашему же домену.
    if (request.method === "POST") {
      const photoUrl = `${url.origin}/welcome.jpg`;
      const bot = createBot(env, photoUrl);
      const handle = webhookCallback(bot, "cloudflare-mod", {
        secretToken: env.WEBHOOK_SECRET,
      });
      return handle(request);
    }

    // Health-check.
    return new Response("Bot is running.", { status: 200 });
  },
};
