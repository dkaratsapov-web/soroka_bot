/**
 * Telegram-бот «лид-магнит за подписку» для Cloudflare Workers (webhook).
 *
 * Логика повторяет leadmagnet_bot.py:
 *   /start            -> если подписан, сразу отдаём материал; иначе показываем кнопки.
 *   кнопка check_sub  -> перепроверяем подписку (getChatMember) и выдаём материал.
 *
 * Зачем Cloudflare: его сеть видит Telegram (нет РФ-тротлинга), сервер не нужен,
 * работает по webhook — это «правильный» прод-режим.
 *
 * Конфиг — через переменные окружения Worker (Settings -> Variables and Secrets):
 *   BOT_TOKEN           (secret)  — токен от @BotFather
 *   CHANNEL                       — @sorokavmarketinge или числовой ID -100...
 *   CHANNEL_URL                   — https://t.me/sorokavmarketinge
 *   LEAD_MAGNET_TEXT              — текст, который получает подписчик
 *   WELCOME_TEXT        (опц.)
 *   NOT_SUBSCRIBED_TEXT (опц.)
 *   WEBHOOK_SECRET      (secret, опц.) — строка для защиты webhook от чужих запросов
 *
 * После деплоя один раз открой в браузере  https://<твой-worker>.workers.dev/setup
 * — это привяжет webhook. И сделай бота администратором канала.
 */

const DEFAULTS = {
  WELCOME_TEXT:
    "Привет! 👋\n\nЧтобы получить бесплатный материал, подпишитесь на канал " +
    "и нажмите «Я подписался».",
  NOT_SUBSCRIBED_TEXT:
    "Кажется, подписки пока нет 🤔\nПодпишитесь и нажмите «Я подписался ✅» ещё раз.",
  LEAD_MAGNET_TEXT:
    "Спасибо за подписку! 🎉\n\nВот ваш материал: https://example.com/your-link",
};

// Вызов Telegram Bot API.
async function tg(env, method, payload) {
  const res = await fetch(
    `https://api.telegram.org/bot${env.BOT_TOKEN}/${method}`,
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    }
  );
  return res.json();
}

function subscribeKeyboard(env) {
  return {
    inline_keyboard: [
      [{ text: "📢 Подписаться на канал", url: env.CHANNEL_URL }],
      [{ text: "Я подписался ✅", callback_data: "check_sub" }],
    ],
  };
}

// true, если пользователь подписан на канал. Любая ошибка (часто — бот не админ) => false.
async function isSubscribed(env, userId) {
  try {
    const r = await tg(env, "getChatMember", {
      chat_id: env.CHANNEL,
      user_id: userId,
    });
    if (!r.ok) return false;
    const status = r.result && r.result.status;
    return status !== "left" && status !== "kicked";
  } catch (e) {
    return false;
  }
}

async function sendLeadMagnet(env, chatId) {
  await tg(env, "sendMessage", {
    chat_id: chatId,
    text: env.LEAD_MAGNET_TEXT || DEFAULTS.LEAD_MAGNET_TEXT,
  });
}

async function handleUpdate(env, update) {
  // /start
  if (update.message && (update.message.text || "").startsWith("/start")) {
    const msg = update.message;
    if (await isSubscribed(env, msg.from.id)) {
      await sendLeadMagnet(env, msg.chat.id);
    } else {
      await tg(env, "sendMessage", {
        chat_id: msg.chat.id,
        text: env.WELCOME_TEXT || DEFAULTS.WELCOME_TEXT,
        reply_markup: subscribeKeyboard(env),
      });
    }
    return;
  }

  // Кнопка «Я подписался ✅»
  if (update.callback_query && update.callback_query.data === "check_sub") {
    const cb = update.callback_query;
    if (await isSubscribed(env, cb.from.id)) {
      await tg(env, "answerCallbackQuery", { callback_query_id: cb.id });
      // Прячем сообщение с кнопками (не критично, если не выйдет).
      await tg(env, "deleteMessage", {
        chat_id: cb.message.chat.id,
        message_id: cb.message.message_id,
      });
      await sendLeadMagnet(env, cb.message.chat.id);
    } else {
      await tg(env, "answerCallbackQuery", {
        callback_query_id: cb.id,
        text: env.NOT_SUBSCRIBED_TEXT || DEFAULTS.NOT_SUBSCRIBED_TEXT,
        show_alert: true,
      });
    }
    return;
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Привязать webhook: открой .../setup в браузере ОДИН раз после деплоя.
    if (request.method === "GET" && url.pathname === "/setup") {
      if (!env.BOT_TOKEN) {
        return new Response("BOT_TOKEN не задан в переменных Worker.", {
          status: 500,
        });
      }
      const r = await tg(env, "setWebhook", {
        url: `${url.origin}/`,
        secret_token: env.WEBHOOK_SECRET || undefined,
        drop_pending_updates: true,
      });
      return new Response(JSON.stringify(r, null, 2), {
        headers: { "content-type": "application/json; charset=utf-8" },
      });
    }

    // Проверка живости.
    if (request.method === "GET") {
      return new Response(
        "Lead-magnet bot is running. Открой /setup один раз, чтобы привязать webhook."
      );
    }

    // Входящие апдейты от Telegram (POST).
    if (request.method === "POST") {
      if (
        env.WEBHOOK_SECRET &&
        request.headers.get("x-telegram-bot-api-secret-token") !==
          env.WEBHOOK_SECRET
      ) {
        return new Response("forbidden", { status: 403 });
      }
      let update;
      try {
        update = await request.json();
      } catch {
        return new Response("bad request", { status: 400 });
      }
      // Telegram всегда отвечаем 200 — иначе он будет ретраить апдейт.
      try {
        await handleUpdate(env, update);
      } catch (e) {
        // Единичная ошибка не должна ронять webhook.
      }
      return new Response("ok");
    }

    return new Response("method not allowed", { status: 405 });
  },
};
