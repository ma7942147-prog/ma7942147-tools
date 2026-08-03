# 全域設定（所有專案共用）

> 這份檔案要放在 `~/.claude/CLAUDE.md`（Windows：`C:\Users\<你的帳號>\.claude\CLAUDE.md`）。
> 來源：《AI Agent 全域設定規範》三師爸 Sense Bar，2026-07-12。
> 主檔在 `ma7942147-tools/tools/agent-setup/全域設定/CLAUDE_global.md`，改這裡才是改本體。

---

## 一、語音回覆

### 觸發時機
使用者說「用語音回答」「唸出來」「唸給我聽」「用語音講結論」時才執行，其餘一律純文字。

### 工具
統一用 **Edge-TTS**（免費、微軟雲端語音合成）。
**不用** SAPI 離線語音、**不開**外部播放器視窗。

執行方式：

```powershell
.\.venv\Scripts\python.exe tools\agent-setup\全域設定\speak.py "要唸的內容"
```

沒有 `.venv` 或沒裝 edge-tts 時：

```powershell
uv pip install --python .\.venv\Scripts\python.exe edge-tts
```

### 講稿撰寫規則
- 口語化、精簡，**100–250 字**
- 數字用中文（講「五十頁」，不要寫「50頁」）
- 只講**結論與下一步**，細節留在文字回覆裡

### 聲音
預設 `zh-TW-YunJheNeural`（男聲、穩重、適合教學）。使用者明確指定才換。

| 聲音代碼 | 性別 | 風格 |
|----------|------|------|
| `zh-TW-YunJheNeural` | 男 | 穩重、適合教學（**預設**） |
| `zh-TW-HsiaoChenNeural` | 女 | 活潑、清晰 |
| `zh-TW-HsiaoYuNeural` | 女 | 溫柔、柔和 |

完整清單：`edge-tts --list-voices`。

使用者說「用三師爸的聲音」→ 那要另外的 voice-clone 技能（VoxCPM2），**不在這份規範範圍**，直接說明並改用預設聲音。

### 播放
一律行內播放，不開外部視窗。播完回報「語音已播放」四個字即可，**不要重複唸過的文字內容**。

---

## 二、開工與收工

### 開工
使用者說「開工」「我來了」「上次做到哪」時，依序做：

1. 確認工作目錄是否在 Google Drive 的 git repo 內
2. 讀 Obsidian 工作筆記的「上次做到哪」+「下一步」
3. `git status` 檢查本地變動
4. 檢查遠端有沒有新 commit —— **有就提醒，不要自動 pull**
5. 回報結構化摘要

### 收工
使用者說「收工」「下班」「結束」時，依序做：

1. 專案 Git 同步：`git status` → 提出 commit 訊息 → **等使用者確認** → push
2. Claude 設定同步：`chezmoi status` → 有變動就 commit + push
3. 提醒還沒進 chezmoi 的敏感檔案（API key 之類）
4. 更新 Obsidian 工作筆記
5. 回報 checklist

---

## 三、語音輸入的錯字還原

使用者常用語音輸入，轉出來的文字會有同音錯字：

| 語音轉出的字 | 實際意思 |
|--------------|---------|
| Call Desk / 摳德斯 | Codex |
| Cloud Call / Cloud Code | Claude Code |
| Typeless | headless |
| antigrity / 安提 | Antigravity |
| 切磨伊 | chezmoi |

**處理原則**：
- 以上下文**善意還原**最合理的原意，不要逐字照字面理解
- 明顯錯字直接順過去，不用每個都拿出來講
- 但**關鍵詞**（檔名、路徑、指令名）若沒把握，**先說出你的理解再往下做**

---

## 四、跨裝置同步

| 同步層 | 內容 | 工具 | 頻率 |
|--------|------|------|------|
| 自動 | 專案檔案 | Google Drive | 即時 |
| 自動 | Claude Code 設定 | Chezmoi | 換電腦時 `chezmoi update` |
| 半自動 | Obsidian 筆記 | Vault 同步 | 確認同步完成 |
| 手動 | GitHub repo | Git | `git pull` / `git push` |
| 手動 | 其他 Agent 設定 | 人工複製 | 設定變更時 |

### 換電腦 checklist
- [ ] `chezmoi update`（同步 Claude Code 設定）
- [ ] 確認 `.venv` 已建立（`uv venv .venv --python 3.12`）
- [ ] 安裝核心套件（`uv pip install -r requirements-core.txt`）
- [ ] 檢查 API key 檔案還在不在
- [ ] 手動同步其他 Agent 的 custom instructions（Codex、Antigravity 沒有自動同步）
