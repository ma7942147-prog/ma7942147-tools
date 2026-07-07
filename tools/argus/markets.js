// 行情資料來源（全部免費、免金鑰）
//   BTC/USD ← Binance klines（穩定、真 K 棒）
//   XAU/USD ← Yahoo Finance chart API（黃金期貨 GC=F，免金鑰）
//
// 每個 market 提供 fetchCandles(interval) 回傳由舊到新的 [{t,o,h,l,c}]，
// t 為毫秒 epoch。抓不到時 throw，交給引擎記 log 並在下輪重試。

const MARKETS = [
  {
    symbol: 'BTC/USD', code: 'B', name: '比特幣', accent: '#f59e0b',
    source: 'binance', binanceSymbol: 'BTCUSDT', decimals: 2,
  },
  {
    symbol: 'XAU/USD', code: 'Au', name: '現貨黃金', accent: '#eab308',
    source: 'yahoo', yahooSymbol: 'GC=F', decimals: 2,
  },
];

async function fetchJson(url) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 12000);
  try {
    const res = await fetch(url, {
      signal: ctrl.signal,
      headers: { 'User-Agent': 'Mozilla/5.0 (ARGUS signal engine)' },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } finally {
    clearTimeout(timer);
  }
}

// Binance interval 對照：'5m' / '15m' 直接可用
async function binanceCandles(sym, interval, limit = 100) {
  const url = `https://api.binance.com/api/v3/klines?symbol=${sym}&interval=${interval}&limit=${limit}`;
  const rows = await fetchJson(url);
  return rows.map(r => ({
    t: r[0], o: +r[1], h: +r[2], l: +r[3], c: +r[4],
  }));
}

// Yahoo chart interval：5m/15m；range 給 5d 拿足夠 K 棒
async function yahooCandles(sym, interval) {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?interval=${interval}&range=5d`;
  const data = await fetchJson(url);
  const r = data?.chart?.result?.[0];
  if (!r) throw new Error('Yahoo: empty result');
  const ts = r.timestamp || [];
  const q = r.indicators?.quote?.[0] || {};
  const out = [];
  for (let i = 0; i < ts.length; i++) {
    const o = q.open?.[i], h = q.high?.[i], l = q.low?.[i], c = q.close?.[i];
    if ([o, h, l, c].some(v => v == null)) continue; // Yahoo 常有 null 間隙
    out.push({ t: ts[i] * 1000, o, h, l, c });
  }
  if (!out.length) throw new Error('Yahoo: no valid candles');
  return out;
}

// 展示 / 離線模式：ARGUS_MOCK=1 時用隨機漫步造 K 棒，讓 UI 立刻有東西看、
// 偶爾也會破框發訊，方便無網路或第一次試跑時體驗。
const MOCK_BASE = { 'BTC/USD': 61000, 'XAU/USD': 4050 };
function mockCandles(market, interval, n = 100) {
  const base = MOCK_BASE[market.symbol] || 100;
  const vol = base * 0.004;
  const step = interval === '15m' ? 900000 : 300000;
  const out = [];
  let price = base, t = Date.now() - n * step;
  for (let i = 0; i < n; i++) {
    const drift = (Math.random() - 0.5) * vol;
    const o = price;
    const c = Math.max(1, o + drift);
    const h = Math.max(o, c) + Math.random() * vol * 0.5;
    const l = Math.min(o, c) - Math.random() * vol * 0.5;
    out.push({ t: t += step, o, h, l, c });
    price = c;
  }
  return out;
}

async function fetchCandles(market, interval) {
  if (process.env.ARGUS_MOCK === '1') return mockCandles(market, interval);
  if (market.source === 'binance') return binanceCandles(market.binanceSymbol, interval);
  if (market.source === 'yahoo') return yahooCandles(market.yahooSymbol, interval);
  throw new Error(`未知的資料來源：${market.source}`);
}

module.exports = { MARKETS, fetchCandles };
