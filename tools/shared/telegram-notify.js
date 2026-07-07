// 呼叫 Firebase Cloud Function 發送 Telegram 通知（見 tools/telegram-notifier/README.md）
// 用法：import { notifyTelegram } from "../shared/telegram-notify.js"; notifyTelegram("xxx 完成了！");
const TELEGRAM_NOTIFY_URL = "https://us-central1-my-teaching-tools-77014.cloudfunctions.net/notifyTelegram";

export async function notifyTelegram(message) {
  try {
    await fetch(TELEGRAM_NOTIFY_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
  } catch (err) {
    console.warn("Telegram 通知失敗：", err);
  }
}
