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
- **agent-setup**：外部工具連接設定與記錄，見 `tools/agent-setup/連接記錄.md`
- **wallpaper**：極簡可愛動物桌布產生器（Pillow 純程式畫，不抓網路圖），見 `tools/wallpaper/README.md`

## 已連接的外部服務
- 雲端 Claude Code（OAuth 連接器，同帳號自動同步）：Google Drive、Gmail、Google Calendar、GitHub
- Windows 本機待接：Obsidian MCP、Firebase CLI → 跑 `tools/agent-setup/setup_windows.ps1`
- 詳細記錄（通道／鑰匙／日期／卡關排除）：`tools/agent-setup/連接記錄.md`

## 教學檔案處理核心工具包
Word／Excel／PPT／PDF／圖片／圖表／QR Code／轉 Markdown 的 10 個 Python 套件。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\install_windows.ps1"
```

裝進 repo 的 `.venv`（不污染系統 Python）。跑 Python 一律用 `.\.venv\Scripts\python.exe`。
只裝核心 10 個；pandas、pdfplumber、ocrmypdf、yt-dlp 等選用套件和 Tesseract／Poppler／ffmpeg
等系統工具**預設不裝**，明確要用時再單獨加。清單見 `requirements-core.txt`，驗證跑 `verify_core.py`。

## 全域設定
完整規範在 `tools/agent-setup/全域設定/CLAUDE_global.md`（本機 Claude Code 會裝到 `~/.claude/CLAUDE.md`）。
**雲端 Claude Code（claude.ai/code）讀不到 `~/.claude/`**，所以下面兩條最常用的抄一份在這裡：

### 語音輸入的錯字還原
使用者常用語音輸入，同音錯字要以上下文善意還原，不要照字面理解：

| 語音轉出的字 | 實際意思 |
|--------------|---------|
| Call Desk / 摳德斯 | Codex |
| Cloud Call / Cloud Code | Claude Code |
| Typeless | headless |
| antigrity / 安提 | Antigravity |
| 切磨伊 | chezmoi |

明顯錯字直接順過去；但關鍵詞（檔名、路徑、指令名）沒把握時，**先說出你的理解再往下做**。

### 語音回覆
使用者說「用語音回答」「唸出來」「唸給我聽」時才做語音，工具統一用 Edge-TTS：
`.\.venv\Scripts\python.exe tools\agent-setup\全域設定\speak.py "內容"`
預設聲音 `zh-TW-YunJheNeural`；講稿 100–250 字、數字用中文、只講結論與下一步。

## 工作注意事項
- 個人資料一律去識別化
- commit 訊息要寫清楚做了什麼 + 為什麼
- 收工前說「收工」讓 Claude 同步三方
- 開工：確認目錄 → 讀工作筆記 → `git status` → 檢查遠端新 commit（**提醒即可，不自動 pull**）
