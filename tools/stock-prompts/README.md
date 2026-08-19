# stock-prompts — 美股研究系統（Jenny 八步驟）

把美股 YouTuber Jenny 的「由上而下八步驟選股法」變成**可追蹤、可程式化**的提示詞庫。

- **可追蹤**：每個提示詞都強制輸出固定欄位的 JSON，且一定有 `changed_vs_last`，所以每次執行都能跟上次比對。
- **可程式化**：`prompts.json` 是機器可讀的提示詞包，`render.js` 負責把 `{{變數}}` 換成實際值。

## 八個步驟

| ID | 步驟 | 頻率 | 變數 |
|---|---|---|---|
| S1 | 總體環境 | 每週 | DATE |
| S2 | 找市場主線 | 每月 | DATE |
| S3 | 從新聞找投資線索 | 事件觸發 | DATE, NEWS |
| S4 | 拆產業鏈 | 每季 | DATE, INDUSTRY |
| S5 | 從產業篩公司 | 每季 | DATE, TREND, INDUSTRY |
| S6 | 用財報驗證投資論點 | 每季（財報後） | DATE, TICKER, THESIS, FINANCIALS |
| S7 | 反推市場現在期待什麼 | 每季 | DATE, TICKER, PRICE |
| S8 | 形成決策與推翻條件 | 每季 | DATE, TICKER |
| DAILY | 每日盤前追蹤 | 每天 | DATE, WATCHLIST |
| WEEKLY | 每週複盤 | 每週 | DATE, WATCHLIST |

閉環：**S8 產出的推翻條件 → 每天由 DAILY 逐條檢查 → 觸發時回頭跑 S6/S7/S8。**

## 用法

```bash
node render.js --list                    # 看所有提示詞
node render.js S1                        # DATE 自動帶今天
node render.js S4 --INDUSTRY=電網變壓器
node render.js S6 --TICKER=AVGO --THESIS="..." --FINANCIALS="$(cat q3.txt)"
node render.js S1 | pbcopy               # 直接複製去貼給 AI
```

缺變數會擋下來並列出缺哪些，不會產生半成品提示詞。

## 檔案

```
obsidian/           ← 人看的筆記（單一事實來源），同步到 Obsidian vault
  00_美股研究系統_總覽.md
  01_節奏表_每日每週每月每季.md
  10_S1 ～ 17_S8      八個提示詞本體
  20/21/22           每日、每週、每月每季的組合提示詞
  30_追蹤儀表板.md     Dataview 匯總
  模板_*.md           每次執行要新增的紀錄筆記
prompts.json        ← 由 build-prompts.js 從 obsidian/*.md 自動產生，勿手改
build-prompts.js    ← 重新產生 prompts.json
render.js           ← 渲染提示詞的 CLI
```

**改提示詞的正確流程**：改 `obsidian/*.md` 的 ` ```text ` 區塊 → 跑 `node build-prompts.js` → 同步到 Obsidian。
直接改 `prompts.json` 會在下次 build 時被覆蓋。

## Obsidian 位置

vault `0.0第二大腦——Obsidian` 底下的 `美股研究系統_Jenny八步驟/`。
紀錄筆記寫進 `每日筆記/`（`美股-YYYY-MM-DD.md`、`美股週報-YYYY-Www.md`）。

## 之後可以接的東西

- 用 `tools/shared/telegram-notify.js` 在每日追蹤有 `alerts > 0` 時推播
- 排程每天早上自動跑 DAILY，把 JSON 寫進 Firestore 存歷史

## ⚠️

研究流程與提示詞模板，不是投資建議。AI 輸出一律要自己回頭核對原始資料來源。
