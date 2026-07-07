// 伺服器端 Telegram 推播：沿用已部署的 notifyTelegram Cloud Function
// （見 tools/telegram-notifier/README.md）。預設會私訊 @ma7942147_bot。
//
// 想改推到別的地方時，設環境變數：
//   ARGUS_TG_URL   自訂 function URL（預設為下方 DEFAULT_URL）
//   ARGUS_TG_MUTE  設為 "1" 則只印在 console、不真的送出（測試用）

const DEFAULT_URL =
  'https://us-central1-my-teaching-tools-77014.cloudfunctions.net/notifyTelegram';

const URL = process.env.ARGUS_TG_URL || DEFAULT_URL;
const MUTE = process.env.ARGUS_TG_MUTE === '1';

async function notifyTelegram(message) {
  if (MUTE) {
    console.log('[TG muted]\n' + message + '\n');
    return true;
  }
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 12000);
    const res = await fetch(URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
      signal: ctrl.signal,
    });
    clearTimeout(timer);
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
    return true;
  } catch (err) {
    console.warn('Telegram 推播失敗：', err.message);
    return false;
  }
}

module.exports = { notifyTelegram };
