// ARGUS 破框策略（Box Breakout + Retest）
//
// 概念（對照 Telegram 訊號畫面）：
//   1. 用最近 LOOKBACK 根 K 棒圍出一個「框」(box)：框頂 = 區間最高、框底 = 區間最低。
//   2. 當前這根 K 棒「收盤」突破框緣 → 產生破框訊號（收盤價 > 框頂 = LONG，< 框底 = SHORT）。
//   3. 進場採「回測破框價」：entry = 被突破的框緣（等回踩再進，勝率較高）。
//   4. 止損放框的另一側 + 緩衝；停利用 R:R 1:1 (TP1)、1:2 (TP2)。
//   5. 可選：用較高週期(15m)的趨勢方向過濾，只做順勢破框。
//
// 這支檔案不碰網路、不碰 Telegram，純函式，方便單獨測試與調參數。

const CONFIG = {
  LOOKBACK: 20,            // 建框用的 K 棒數
  MIN_BREAK_RATIO: 0.02,   // 突破幅度需 > 框高 * 此比例，濾掉假突破
  STOP_BUFFER_RATIO: 0.10, // 止損在框外再加 框高 * 此比例 的緩衝
  TP1_RR: 1,               // TP1 的 風報比倍數
  TP2_RR: 2,               // TP2 的 風報比倍數
  REQUIRE_TREND: true,     // 是否要求順著高週期趨勢
};

// 簡單 EMA，用來判高週期趨勢方向
function ema(values, period) {
  if (values.length < period) return null;
  const k = 2 / (period + 1);
  let e = values.slice(0, period).reduce((a, b) => a + b, 0) / period;
  for (let i = period; i < values.length; i++) e = values[i] * k + e * (1 - k);
  return e;
}

// 回傳高週期趨勢：'up' | 'down' | 'flat'
function trendOf(htfCandles) {
  if (!htfCandles || htfCandles.length < 25) return 'flat';
  const closes = htfCandles.map(c => c.c);
  const fast = ema(closes, 9);
  const slow = ema(closes, 21);
  if (fast == null || slow == null) return 'flat';
  const diff = (fast - slow) / slow;
  if (diff > 0.0005) return 'up';
  if (diff < -0.0005) return 'down';
  return 'flat';
}

// 主判定。candles = 由舊到新的 5m K 棒陣列 [{t,o,h,l,c}]；htfCandles = 高週期(15m)，可為 null。
// 有訊號回傳 signal 物件；沒訊號回傳 null。
function analyze(candles, htfCandles, cfg = CONFIG) {
  if (!candles || candles.length < cfg.LOOKBACK + 2) return null;

  const recent = candles.slice(-(cfg.LOOKBACK + 1));
  const box = recent.slice(0, cfg.LOOKBACK); // 建框：不含當前這根
  const cur = recent[recent.length - 1];     // 當前剛收的 K 棒

  const boxHigh = Math.max(...box.map(c => c.h));
  const boxLow = Math.min(...box.map(c => c.l));
  const boxRange = boxHigh - boxLow;
  if (boxRange <= 0) return null;

  let dir = null, breakLevel = null;
  if (cur.c > boxHigh) { dir = 'LONG'; breakLevel = boxHigh; }
  else if (cur.c < boxLow) { dir = 'SHORT'; breakLevel = boxLow; }
  else return null;

  // 濾假突破：突破幅度不夠就不算
  const breakoutDist = dir === 'LONG' ? cur.c - boxHigh : boxLow - cur.c;
  if (breakoutDist < boxRange * cfg.MIN_BREAK_RATIO) return null;

  // 順勢過濾
  if (cfg.REQUIRE_TREND) {
    const trend = trendOf(htfCandles);
    if (dir === 'LONG' && trend === 'down') return null;
    if (dir === 'SHORT' && trend === 'up') return null;
  }

  const entry = breakLevel; // 回測破框價進場
  const buffer = boxRange * cfg.STOP_BUFFER_RATIO;
  const stop = dir === 'LONG' ? boxLow - buffer : boxHigh + buffer;
  const risk = Math.abs(entry - stop);
  if (risk <= 0) return null;

  const tp1 = dir === 'LONG' ? entry + risk * cfg.TP1_RR : entry - risk * cfg.TP1_RR;
  const tp2 = dir === 'LONG' ? entry + risk * cfg.TP2_RR : entry - risk * cfg.TP2_RR;

  return {
    dir, entry, stop, tp1, tp2,
    boxHigh, boxLow,
    curHigh: cur.h, curLow: cur.l,
    breakLevel,
    rr1: cfg.TP1_RR, rr2: cfg.TP2_RR,
    confirmedAt: cur.t, // 破框確認時間（該 K 棒收盤時間）
  };
}

module.exports = { analyze, trendOf, ema, CONFIG };
