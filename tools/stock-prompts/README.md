# stock-prompts — 台股研究系統（Jenny 八步驟改台股版）

把美股 YouTuber Jenny 的「由上而下八步驟選股法」變成**可追蹤、可程式化**的提示詞庫。

筆記全部用白話寫，看不懂金融術語也能直接照著做。

## 八個步驟在問什麼

| ID | 白話講就是 | 多久做一次 | 要填的變數 |
|---|---|---|---|
| S1 | 現在市場喜歡什麼樣的公司 | 每週 | DATE |
| S2 | 未來 3–5 年什麼東西會一直有人買 | 每月 | DATE |
| S3 | 我看到的這則新聞重要嗎 | 看到新聞時 | DATE, NEWS |
| S4 | 這個產業裡錢最後被誰賺走 | 每季 | DATE, INDUSTRY |
| S5 | 誰最會把生意變成錢 | 每季 | DATE, TREND, INDUSTRY |
| S6 | 財報有沒有打臉我原本的想法 | 每季（財報後） | DATE, TICKER, THESIS, FINANCIALS |
| S7 | 現在這個股價是不是太貴了 | 每季 | DATE, TICKER, PRICE |
| S8 | 發生什麼事我該承認自己看錯 | 每季 | DATE, TICKER |
| DAILY | 每天早上 10 分鐘檢查 | 每天 | DATE, WATCHLIST |
| WEEKLY | 每週日 30 分鐘複盤 | 每週 | DATE, WATCHLIST |

## 閉環設計

**S8 產出可量化的警戒線 → 每天早上由 DAILY 逐條檢查 → 踩到才回頭跑 S6/S7/S8。**

沒有這個閉環，每天看盤就只是看盤。

## 用法

```bash
node render.js --list                      # 看所有提示詞
node render.js S1                          # DATE 自動帶今天
node render.js S4 --INDUSTRY=資料中心散熱
node render.js S6 --TICKER=AVGO --THESIS="..." --FINANCIALS="$(cat q3.txt)"
node render.js S1 | pbcopy                 # 直接複製去貼給 AI
```

缺變數會擋下來並列出缺哪些，不會產生半成品提示詞。

## 檔案

```
obsidian/                        ← 人看的筆記（單一事實來源），同步到 Obsidian vault
  ★從這裡開始.md                   先看這個
  每天早上做的事.md
  每週日做的事.md
  每月每季做的事.md
  步驟1～步驟8-*.md                八個提示詞本體
  我的追蹤表.md                    股票清單、警戒線、Dataview 統計
  模板-*.md                       每天／每週／個股的空白記錄表
prompts.json                     ← build-prompts.js 自動產生，勿手改
build-prompts.js                 ← 重新產生 prompts.json
render.js                        ← 渲染提示詞的 CLI
```

### 筆記的雙層結構

每個步驟的筆記裡有**兩個** ` ```text ` 區塊：

1. **主提示詞** — 純白話，沒有 JSON，給人直接複製貼給 AI
2. **「想存檔做長期比較的話」** — 附加的 JSON 輸出要求，標明可選

`build-prompts.js` 會把**兩塊都抓出來接在一起**寫進 `prompts.json`，
因為程式化使用時一定要 JSON 才能比對歷次結果。
人看的時候可以只用第一塊，不影響使用。

**改提示詞的正確流程**：改 `obsidian/*.md` 的 ` ```text ` 區塊 → 跑 `node build-prompts.js` → 同步到 Obsidian。
直接改 `prompts.json` 會在下次 build 時被覆蓋。

## Obsidian 位置

vault `0.0第二大腦——Obsidian` 底下的 `台股研究系統_Jenny八步驟/`。
每天／每週的記錄寫進 `每日筆記/`（`美股-YYYY-MM-DD.md`、`美股週報-YYYY-Www.md`）。

## 跟既有決策卡的接點

vault 裡原本那套「灰度思考／彩虹下注」決策卡（`時間投顧_廖國峰先生_價值投資`）負責
**決定下多少**；這套負責**找標的、算出上下檔**：

- S7 的悲觀／正常／樂觀價 → 決策卡的 `intrinsic_conservative / base / optimistic`
- S7 的上檔、下檔 → 凱利公式的 `b` 與 `loss`（護欄照舊：`b ≤ 0` 不下注）
- S8 的警戒線 → 決策卡的「會推翻此決策的觸發條件」

## 之後可以接的東西

- 用 `tools/shared/telegram-notify.js` 在每日檢查有警戒時推播
- 排程每天早上自動跑 DAILY，把 JSON 寫進 Firestore 存歷史

## ⚠️

研究流程與提示詞模板，不是投資建議。AI 輸出一律要自己回頭核對原始資料來源。
