# agent-setup — 外部工具連接

依 `2.AGENT_SETUP_外部工具連接指南.md`（三師爸 Sense Bar EP04）做的連接設定與記錄。

## 檔案

| 檔案 | 用途 |
|------|------|
| `連接記錄.md` | 接了哪些服務、走哪條通道、用哪種鑰匙、日期。**換電腦先讀這份** |
| `setup_windows.ps1` | 在 Windows 本機接上 Obsidian MCP 與 Firebase 的安裝腳本 |
| `全域設定/` | 語音回覆 + 開工收工 + 錯字還原的全域規範，見該資料夾的 `README.md` |

## 現在的狀況

**雲端 Claude Code（claude.ai/code）已經接好的**——不用做任何事：
Google Drive、Gmail、Google Calendar、GitHub。這些是 claude.ai 網頁上的 Connectors，
同帳號自動同步進來，走 OAuth。已實測可讀取 Drive 檔案、可讀寫本 repo。

**還要在你 Windows 電腦上接的**：Obsidian、Firebase。
這兩個要碰本機檔案／本機憑證，雲端容器看不到你的硬碟，所以只能在本機裝。

## 在 Windows 上怎麼跑

先確認電腦有 Node.js（沒有的話去 https://nodejs.org/ 裝 LTS，裝完重開終端機）。

然後在本 repo 根目錄開 PowerShell：

```powershell
# 先空跑看看環境有沒有問題，不會真的安裝
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\tools\agent-setup\setup_windows.ps1" -DryRun

# 確認沒問題後，帶上你的 Obsidian vault 路徑正式安裝
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\tools\agent-setup\setup_windows.ps1" -VaultPath "C:\Users\你的帳號\Documents\第二大腦"
```

vault 路徑就是 Obsidian 左下角「管理保管庫」看到的那個資料夾。

### 裝完一定要做

1. **完全關掉 Claude Code 再重開**（不重啟，MCP 不會生效——這是最常見的卡關）
2. 重開後問一句：「你現在看得到哪些 MCP 工具？」
3. Firebase 第一次用：終端機跑 `firebase login`，瀏覽器授權一次

## 為什麼選這些套件

指南的安全守則說「來路不明的 MCP server 不裝，優先官方或高星數專案」，所以：

- **Obsidian** → 用官方 `@modelcontextprotocol/server-filesystem` 指到 vault 資料夾。
  Obsidian vault 本質就是一堆 `.md` 檔的資料夾，官方 filesystem server 就夠用，
  不必裝第三方的 obsidian-mcp。免鑰匙。
- **Firebase** → 官方 `firebase-tools` CLI 內建 `firebase experimental:mcp`，
  不用另外找套件。走 `firebase login` 的 OAuth，**不要**下載服務帳戶 JSON 金鑰放進 repo。

## 安全

`.gitignore` 已擋掉 `.env`、`*.key`、`credentials.*`、`.claude/`，金鑰不會誤傳進這個公開 repo。
