# 全域設定

依《AI Agent 全域設定規範》（三師爸 Sense Bar，2026-07-12）做的多 Agent 共用設定：
語音回覆（Edge-TTS）、開工／收工流程、語音輸入錯字還原、跨電腦同步（chezmoi）。

## 檔案

| 檔案 | 給誰用 | 怎麼生效 |
|------|--------|----------|
| `CLAUDE_global.md` | Claude Code | 複製到 `~/.claude/CLAUDE.md`（腳本會做） |
| `antigravity_system_prompt.md` | Google Antigravity | **人工複製貼上**到 System Prompt |
| `speak.py` | 兩者共用 | Edge-TTS 語音合成 + 行內播放 |
| `setup_global_windows.ps1` | Windows 本機 | 一鍵完成上面前三項 |

## 怎麼裝

在你 Windows 電腦上，本 repo 根目錄開 PowerShell：

```powershell
# 先空跑，看看會動到什麼
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\tools\agent-setup\全域設定\setup_global_windows.ps1" -DryRun

# 正式安裝
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\tools\agent-setup\全域設定\setup_global_windows.ps1"
```

腳本做四件事：

1. 把 `CLAUDE_global.md` 複製到 `~/.claude/CLAUDE.md`（已有舊檔會先備份成 `.bak-<時間>`）
2. 建 `.venv` 並裝 `edge-tts`，然後**實測合成一句話**確認語音真的能出聲
3. 裝 chezmoi，把 `~/.claude/CLAUDE.md` 納入追蹤
4. 開啟 Antigravity 那份檔案，提醒你去貼

裝完 **完全關掉 Claude Code 再重開**，全域設定才會生效。

## Antigravity 為什麼要人工貼

Antigravity 的 custom instructions 存在 App 內部，沒有一個檔案可以讓腳本寫入
（規範原文也註明「無自動同步機制」）。所以只能：

`Settings` → `Customizations` → `System Prompt` → 貼上 `antigravity_system_prompt.md`
裡分隔線以下的全部內容。

## 語音怎麼用

```powershell
# 用預設男聲唸
.\.venv\Scripts\python.exe tools\agent-setup\全域設定\speak.py "設定完成，可以開始工作了。"

# 換女聲
.\.venv\Scripts\python.exe tools\agent-setup\全域設定\speak.py "測試" --voice zh-TW-HsiaoChenNeural

# 只存檔不播放
.\.venv\Scripts\python.exe tools\agent-setup\全域設定\speak.py "測試" --output out.mp3

# 看有哪些中文聲音
.\.venv\Scripts\python.exe tools\agent-setup\全域設定\speak.py --list-voices
```

播完會自動刪掉暫存 mp3，不會在硬碟堆一堆 `temp_speech.mp3`。

## 兩個要注意的地方

**1. `chezmoi init` 不要照抄規範原文。**
原文寫 `chezmoi init mathruffian-dot` —— 那是講師本人的 dotfiles repo，
照抄會把別人的設定拉下來蓋掉你的。要改成你自己的：

```powershell
chezmoi init <你的GitHub帳號>/dotfiles
```

沒有 dotfiles repo 就先去 GitHub 開一個（建議設 private，因為 `~/.claude/` 可能含 token）。
腳本偵測到還沒初始化時會停下來提醒，不會自己亂 init。

**2. 雲端 Claude Code 讀不到 `~/.claude/CLAUDE.md`。**
claude.ai/code 每次都開新容器，家目錄不會保留。所以語音錯字還原、語音回覆這兩條
另外抄了一份在 repo 根目錄的 `CLAUDE.md` 裡——那份雲端讀得到。
**改規則時兩邊都要改。**

## 規範原文的小問題

原文「常用聲音」表格裡 `zh-TW-YunJheNeural` 出現兩次（第 1 列和第 3 列），
第 3 列應該是別的聲音。本專案的表只留三個實際不同的聲音。
