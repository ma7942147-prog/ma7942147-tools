# ma7942147-tools — 我的工具總專案

## 對話開始時請先讀
進度與最近更動都在 Obsidian：`第二大腦/ma7942147-tools/工作筆記.md`

## 工作模式
- **加新工具**：對 Claude 說「我想做一個 XXX 工具」→ Claude 會建 `tools/<工具名>/` 子資料夾
- **結束工作**：對 Claude 說「收工」→ 自動 commit + push + 更新 Obsidian 工作筆記
- **接續工作**：對 Claude 說「開工」或「讀工作筆記、告訴我上次做到哪」

## 工作桌 + 三個家
- 📋 GDrive 工作桌：`G:\我的雲端硬碟\ma7942147-tools\`（自動跨電腦同步）
- 🐙 GitHub repo：`ma7942147-prog/ma7942147-tools`（公開，網頁的家）
- 📘 Obsidian 駕駛艙：`第二大腦/ma7942147-tools/工作筆記.md`（想法的家）
- 🔥 Firebase 專案：`my-teaching-tools-77014`（資料的家）

## 工具清單
（之後加新工具時會自動更新）
- **mv-creator**：MV 創作追蹤器（主題→歌詞→曲風→Suno→Grok 影片）
- **edu-video-maker**：影音教學 Agent 工作室（腳本→語音→影片）
- **telegram-notifier**：共用的 Telegram 通知基礎設施（`/functions` + `tools/shared/telegram-notify.js`），部署步驟見 `tools/telegram-notifier/README.md`；bot 是 @ma7942147_bot
- **carousel-maker**：教學型輪播圖產生器（改 JSON→匯出 Threads/IG 直式 1080×1350 PNG），純瀏覽器離線可用，見 `tools/carousel-maker/README.md`

## 工作注意事項
- 個人資料一律去識別化
- commit 訊息要寫清楚做了什麼 + 為什麼
- 收工前說「收工」讓 Claude 同步三方
