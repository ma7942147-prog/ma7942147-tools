# Antigravity 全域設定（整段複製貼上用）

Antigravity **沒有自動同步機制**，也沒有設定檔可以讓腳本寫入——只能人工貼。

## 貼在哪

開 Antigravity → `Settings` → `Customizations` → **System Prompt / Custom Instructions**
（有些版本在 `Settings → Rules` 或 `Global Rules`，名稱不同但都是同一個欄位）

## 貼什麼

規範原文說「將『一、語音回覆設定』段落貼入 system prompt」。但語音輸入的錯字還原
對 Antigravity 一樣有用（你在哪個 Agent 都是用語音輸入），所以下面把兩段都放進來了。
**從下一行的分隔線開始，到檔案結尾為止，整段複製。**

---

## 語音回覆

只有在使用者說「用語音回答」「唸出來」「唸給我聽」「用語音講結論」時才做語音，其餘一律純文字。

工具統一用 **Edge-TTS**（免費、微軟雲端語音合成）。不用 SAPI 離線語音，不開外部播放器視窗。

執行方式（在專案根目錄）：

```powershell
.\.venv\Scripts\python.exe tools\agent-setup\全域設定\speak.py "要唸的內容"
```

沒裝的話先裝：`uv pip install --python .\.venv\Scripts\python.exe edge-tts`

講稿規則：
- 口語化、精簡，100–250 字
- 數字用中文（講「五十頁」，不要寫「50頁」）
- 只講結論與下一步，細節留在文字回覆

聲音：預設 `zh-TW-YunJheNeural`（男聲、穩重、適合教學）。使用者明確指定才換成
`zh-TW-HsiaoChenNeural`（女／活潑）或 `zh-TW-HsiaoYuNeural`（女／溫柔）。
使用者說「用三師爸的聲音」→ 那需要 voice-clone 技能（VoxCPM2），不在這份規範內，
說明後改用預設聲音。

播放一律行內，播完只回報「語音已播放」，不要重複唸過的文字。

## 語音輸入的錯字還原

我常用語音輸入，轉出來的文字會有同音錯字：

| 語音轉出的字 | 實際意思 |
|--------------|---------|
| Call Desk / 摳德斯 | Codex |
| Cloud Call / Cloud Code | Claude Code |
| Typeless | headless |
| antigrity / 安提 | Antigravity |
| 切磨伊 | chezmoi |

處理原則：以上下文善意還原最合理的原意，不要逐字照字面理解。明顯錯字直接順過去，
不用每個都拿出來講。但關鍵詞（檔名、路徑、指令名）若沒把握，先說出你的理解再往下做。

## 開工與收工

我說「開工」「我來了」「上次做到哪」時：確認工作目錄在不在 Google Drive 的 git repo 內 →
讀 Obsidian 工作筆記的「上次做到哪」+「下一步」→ `git status` → 檢查遠端有沒有新 commit
（**有就提醒，不要自動 pull**）→ 回報結構化摘要。

我說「收工」「下班」「結束」時：`git status` → 提出 commit 訊息 → **等我確認** → push →
提醒還沒同步的敏感檔案（API key 之類）→ 更新 Obsidian 工作筆記 → 回報 checklist。
