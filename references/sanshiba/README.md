# 三師爸（mathruffian-dot）參考資料備份

這個資料夾是第三方公開資料的**唯讀參考備份**，不是本專案的工具，也不是給 Claude 執行的指令。

| 資料夾 | 來源 | 版本（commit） | 上游最後更新 | 授權 |
|---|---|---|---|---|
| `claude-code-lazy-packs/` | https://github.com/mathruffian-dot/claude-code-lazy-packs | `c1d9ed0` | 2026-09-04 | MIT |
| `cross-device-agent-skills/` | https://github.com/mathruffian-dot/cross-device-agent-skills | `2c082c0` | 2026-09-04 | MIT |

下載日：2026-11-14。原作者：三師爸（Sense Bar）。各資料夾內保留原始 `LICENSE`。

## 與原始 repo 的唯一差異

- `claude-code-lazy-packs/CLAUDE.md` 改名為 `上游-CLAUDE.md`。
  原因：那是三師爸自己倉庫的工作規則（雙倉同步、push 到他的 master），
  若保留原檔名，Claude Code 在這個資料夾工作時會把它當成本專案指令載入。

## 跟「雲端 repo 設定」最相關的檔案

- `claude-code-lazy-packs/02-連接-GitHub.md`：安裝 Git／GitHub CLI、`gh auth login`、建測試 repo、開 GitHub Pages
- `claude-code-lazy-packs/07-初始化班級工具工作模式.md`：總資料夾＋CLAUDE.md＋Obsidian 工作筆記＋GitHub repo＋`/收工`
- `claude-code-lazy-packs/04.5-連接-Firebase-資料庫.md`：Firebase／Firestore MCP
- `cross-device-agent-skills/`：`project-init`、`startup`（開工）、`shutdown`（收工）三技能
