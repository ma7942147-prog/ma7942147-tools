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

// ---------------------------------------------------------------------------
// 紫璃工坊的繪圖代理
// 瀏覽器直接打 x.ai / OpenAI / Gemini 會被 CORS 擋，而且 API Key 得放在前端。
// 這支 function 代打：Key 存在 Firebase secret，前端只送提示詞 + 通行碼。
//
// POST { token, provider, model, prompt, size } -> { dataUrl }
//   token    必填，要等於 secret ZILI_ACCESS_TOKEN（避免公開網址被別人燒點數）
//   provider "xai" | "openai" | "gemini"，預設 xai
//   model    可選，不填用該供應商預設
//   prompt   必填
//   size     可選，"864x1152" 這種格式，只有 OpenAI 會用到
// ---------------------------------------------------------------------------
const IMAGE_API_KEY = defineSecret("IMAGE_API_KEY");
const ZILI_ACCESS_TOKEN = defineSecret("ZILI_ACCESS_TOKEN");

const IMAGE_PROVIDERS = {
  xai: {
    url: "https://api.x.ai/v1/images/generations",
    defaultModel: "grok-2-image-1212",
  },
  openai: {
    url: "https://api.openai.com/v1/images/generations",
    defaultModel: "gpt-image-1",
  },
  gemini: {
    url: "https://generativelanguage.googleapis.com/v1beta/models",
    defaultModel: "gemini-2.5-flash-image",
  },
};

exports.generateImage = onRequest(
  { secrets: [IMAGE_API_KEY, ZILI_ACCESS_TOKEN], cors: true, timeoutSeconds: 120 },
  async (req, res) => {
    if (req.method !== "POST") {
      res.status(405).json({ error: "Method Not Allowed" });
      return;
    }

    const body = req.body || {};
    if (body.token !== ZILI_ACCESS_TOKEN.value()) {
      res.status(401).json({ error: "通行碼不對" });
      return;
    }

    const prompt = (body.prompt || "").trim();
    if (!prompt) {
      res.status(400).json({ error: "缺少 prompt" });
      return;
    }

    const provider = IMAGE_PROVIDERS[body.provider] ? body.provider : "xai";
    const conf = IMAGE_PROVIDERS[provider];
    const model = (body.model || "").trim() || conf.defaultModel;
    const key = IMAGE_API_KEY.value();

    try {
      let dataUrl;

      if (provider === "gemini") {
        const url = `${conf.url}/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(key)}`;
        const r = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] }),
        });
        const j = await r.json();
        if (!r.ok) throw new Error(j.error?.message || `${r.status} ${r.statusText}`);
        const parts = j.candidates?.[0]?.content?.parts || [];
        const inline = parts.map((p) => p.inlineData || p.inline_data).find(Boolean);
        if (!inline) throw new Error("回應裡沒有圖片");
        dataUrl = `data:${inline.mimeType || inline.mime_type || "image/png"};base64,${inline.data}`;
      } else {
        const payload = { model, prompt, n: 1 };
        if (provider === "xai") payload.response_format = "b64_json";
        if (provider === "openai" && body.size) payload.size = body.size;
        const r = await fetch(conf.url, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${key}` },
          body: JSON.stringify(payload),
        });
        const j = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(j.error?.message || j.error || `${r.status} ${r.statusText}`);
        const d = j.data?.[0];
        if (!d) throw new Error("回應裡沒有圖片");
        if (d.b64_json) dataUrl = `data:image/png;base64,${d.b64_json}`;
        else if (d.url) dataUrl = d.url;
        else throw new Error("回應格式看不懂");
      }

      res.status(200).json({ dataUrl });
    } catch (err) {
      res.status(502).json({ error: String(err && err.message ? err.message : err) });
    }
  }
);
