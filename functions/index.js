const { onRequest } = require("firebase-functions/v2/https");
const { defineSecret } = require("firebase-functions/params");

const TELEGRAM_BOT_TOKEN = defineSecret("TELEGRAM_BOT_TOKEN");
const TELEGRAM_CHAT_ID = defineSecret("TELEGRAM_CHAT_ID");

// POST { message: string } -> sends a Telegram message to the configured chat.
// Used by the static tools under tools/ to notify on completion.
exports.notifyTelegram = onRequest(
  { secrets: [TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID], cors: true },
  async (req, res) => {
    if (req.method !== "POST") {
      res.status(405).send("Method Not Allowed");
      return;
    }

    const message = (req.body && req.body.message || "").trim();
    if (!message) {
      res.status(400).send("Missing 'message' in request body");
      return;
    }

    const token = TELEGRAM_BOT_TOKEN.value();
    const chatId = TELEGRAM_CHAT_ID.value();

    const tgRes = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: chatId, text: message }),
    });

    if (!tgRes.ok) {
      const errText = await tgRes.text();
      res.status(502).send(`Telegram API error: ${errText}`);
      return;
    }

    res.status(200).send("OK");
  }
);
