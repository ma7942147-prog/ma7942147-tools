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

## 教學檔案處理「核心工具包」
依《1.AGENT_SETUP_教學檔案處理工具包.md》。**在自己的 Windows 電腦上**、本 repo 根目錄跑：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\install_windows.ps1"
```

- 裝完用 `.\.venv\Scripts\python.exe` 執行本 repo 的 Python 程式（不要用全域 python）
- 核心 10 個套件清單在 `requirements-core.txt`；驗證用 `verify_core.py`
- **選用套件（pandas、pdfplumber、ocrmypdf、edge-tts…）預設不裝**，等真的要用到
  那個任務再單獨裝進同一個 `.venv`
- 系統工具（Tesseract、Poppler、ffmpeg）不是 pip 套件，預設不裝；裝完**必須重開終端機**
- ⚠️ `.venv` 不會跟著 GitHub 或 GDrive 同步（已列入 `.gitignore`）。
  **換一台電腦就要重跑一次上面那行**——雲端會話、WSL、沙盒都不能共用 Windows 的 `.venv`

## 外部工具連接紀錄
（依《AGENT_SETUP 外部工具連接指南》第四步要求記錄；最後查證 2026-08-03）

| 服務 | 通道 | 鑰匙 | 設定位置 | 狀態 |
|------|------|------|----------|------|
| Google Drive | claude.ai 內建連接器 | OAuth | claude.ai `Settings → Connectors` | ✅ 已測通（讀得到雲端硬碟檔案）|
| Gmail | claude.ai 內建連接器 | OAuth | 同上 | ✅ 已連接 |
| Google 日曆 | claude.ai 內建連接器 | OAuth | 同上 | ✅ 已測通（列得出日曆清單）|
| GitHub | claude.ai 內建連接器 | OAuth | 同上 | ✅ 已測通（帳號 ma7942147-prog）|

- 這四個走的都是「內建連接器」路線，**同帳號的 Claude Code 會自動看到，不用再 `claude mcp add`**。
- 目前 `claude mcp list` 是空的，代表沒有任何手動安裝的本地 MCP server——這是正常的。
- 尚未連接：Obsidian（需本機 MCP，指向 vault 路徑）、Firebase（`firebase login` + CLI）。
  這兩個都必須在**自己的 Windows 電腦**上做，雲端會話裝了不會留下來。

## 工作注意事項
- 個人資料一律去識別化
- commit 訊息要寫清楚做了什麼 + 為什麼
- 收工前說「收工」讓 Claude 同步三方
- 金鑰只放本機設定檔或 `.env`，**絕不 commit**（這個 repo 是公開的）
