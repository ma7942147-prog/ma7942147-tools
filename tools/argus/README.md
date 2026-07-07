# 🛰 ARGUS 阿古斯 — AI 破框訊號引擎

一個持續運作的本機服務：**每 5 分鐘**抓即時行情、掃描「破框（box breakout）」型態、
產生「進場 / 止損 / TP1 / TP2 / R:R」訊號、即時推播到 **Telegram**，並提供一個即時儀表板。

> ⚠️ 僅產生型態訊號供研究參考，**不下單、不構成投資建議**。市場有風險，交易請自負盈虧。

## 快速開始

不需要 `npm install`（純 Node 內建模組，需 Node 18+）：

```bash
cd tools/argus
node server.js            # 真行情模式
# 或先看畫面（隨機假資料，不用等、不用網路）：
ARGUS_MOCK=1 node server.js
```

開瀏覽器 → **http://localhost:3002**

## 監控標的與資料來源（免費、免金鑰）

| 標的 | 中文 | 來源 |
|------|------|------|
| BTC/USD | 比特幣 | Binance klines API |
| XAU/USD | 現貨黃金 | Yahoo Finance chart API（黃金期貨 GC=F）|

## 策略：破框 + 回測（`strategy.js`）

1. 用最近 20 根 5m K 棒圍出「框」：框頂＝區間最高、框底＝區間最低。
2. 當前 K 棒**收盤**突破框緣 → 破框（收 > 框頂＝LONG，收 < 框底＝SHORT）。
3. 進場採「**回測破框價**」，止損放框的另一側 + 緩衝。
4. 停利：TP1 = 1×風險（R:R 1:1）、TP2 = 2×風險（R:R 1:2）。
5. 過濾：突破幅度不足的假突破、逆著 15m 趨勢的破框都會被擋掉。
6. **同一商品同時只留 1 筆進行中訊號**（避免多筆同商品訊號互相打架）。

參數都集中在 `strategy.js` 的 `CONFIG`，可自行調整。

## 訊號生命週期

```
破框 → 發訊(pending，等回測) → 回測進場(active) → 觸及 TP2 / 止損 → 結算推播
                                          └ 逾 45 分鐘沒回測 → 自動取消
```

## Telegram 推播

沿用專案既有的 `notifyTelegram` Cloud Function（見 `tools/telegram-notifier/`），
預設**私訊 @ma7942147_bot**。用環境變數調整：

| 變數 | 作用 |
|------|------|
| `ARGUS_TG_MUTE=1` | 只印在 console，不真的送出（測試用）|
| `ARGUS_TG_URL=...` | 改推到自訂的 function URL |
| `ARGUS_MOCK=1` | 用隨機假資料跑，方便離線看 UI |
| `PORT=3002` | 更改埠號（預設 3002）|

## 測試

```bash
node test.js              # 破框策略單元測試
node test-integration.js  # 端到端：破框→發訊→回測→結算 全流程
# 或 npm test 一次跑兩個
```

## 檔案結構

```
argus/
├── server.js       引擎 + 零依賴 HTTP 伺服器（掃描排程、訊號生命週期、/api/state）
├── strategy.js     破框策略（純函式，好調參好測試）
├── markets.js      行情來源（Binance / Yahoo）＋ 假資料模式
├── notify.js       Telegram 推播（接既有 Cloud Function）
├── public/index.html  即時儀表板
├── test.js / test-integration.js
└── data/state.json    執行時狀態（進行中訊號、計數；已 gitignore）
```

## 之後可以加

- 更多標的（在 `markets.js` 的 `MARKETS` 加一筆即可）
- 部署到雲端 24 小時跑（例如 Cloud Run + 排程；本機版適合先驗證策略）
- 勝率 / 累計損益統計頁
