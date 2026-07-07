# Telegram 通知

其他工具（mv-creator、edu-video-maker...）完成事情時，透過這個 Firebase Cloud Function 推播訊息到你的 Telegram bot（@ma7942147_bot / tom ma）。

程式碼在 `/functions`（Cloud Function），共用呼叫端在 `/tools/shared/telegram-notify.js`。

✅ 已部署完成。函式網址：`https://us-central1-my-teaching-tools-77014.cloudfunctions.net/notifyTelegram`
（專案已升級為 Blaze 方案，`TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID` 已存在 Secret Manager）

## 部署步驟（僅供之後重新部署或换電腦參考）

1. 安裝 firebase-tools 並登入（在你自己的電腦上）：
   ```
   npm install -g firebase-tools
   firebase login
   ```

2. 安裝 functions 相依套件：
   ```
   cd functions
   npm install
   ```

3. 設定兩個 secret（互動輸入，不會存進 repo）：
   ```
   firebase functions:secrets:set TELEGRAM_BOT_TOKEN
   ```
   貼上跟 BotFather 拿到的 token（在 @BotFather 對話裡 /mybots → 選 tom ma → API Token）。

   ```
   firebase functions:secrets:set TELEGRAM_CHAT_ID
   ```
   貼上你要接收通知的 chat id。取得方式：先在 Telegram 傳一則訊息給 @ma7942147_bot，再打開
   `https://api.telegram.org/bot<你的TOKEN>/getUpdates`，在回傳 JSON 裡找 `message.chat.id`。

4. 部署：
   ```
   firebase deploy --only functions
   ```
   部署完成後終端機會印出函式的網址，格式類似：
   `https://asia-east1-my-teaching-tools-77014.cloudfunctions.net/notifyTelegram`

5. 把這個網址貼到 `tools/shared/telegram-notify.js` 裡的 `TELEGRAM_NOTIFY_URL`。

## 已接上通知的工具

- `mv-creator`：五個步驟全部勾選完成時，發一次「MV 專案完成」通知
- `edu-video-maker`：Agent A 腳本生成成功時，發一次通知

之後新工具想加通知，直接 `import { notifyTelegram } from "../shared/telegram-notify.js"` 呼叫即可。
