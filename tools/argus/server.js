// ARGUS 阿古斯 — AI 交易訊號引擎
//
// 一個持續運作的本機服務：每 5 分鐘抓即時行情、掃描「破框」型態、
// 產生進場/止損/停利訊號、推播到 Telegram，並提供一個即時儀表板。
//
// 執行：  node server.js        （不需 npm install，純 Node 內建模組）
// 開啟：  http://localhost:3002
//
// 免責：本工具只產生「訊號」供研究參考，不下單、不構成投資建議。

const http = require('http');
const fs = require('fs');
const path = require('path');
const { MARKETS, fetchCandles } = require('./markets');
const { analyze } = require('./strategy');
const { notifyTelegram } = require('./notify');

const PORT = process.env.PORT || 3002;
const SCAN_INTERVAL_MS = 5 * 60 * 1000;      // 每 5 分鐘掃描一次
const COOLDOWN_MS = 60 * 60 * 1000;          // 同商品發訊後冷卻 60 分鐘
const PENDING_TIMEOUT_MS = 45 * 60 * 1000;   // 掛單等回測逾時（未回測就取消）
const DATA_FILE = path.join(__dirname, 'data', 'state.json');
const MAX_LOG = 60;
const MAX_SIGNAL_HISTORY = 30;

// ---------- 狀態 ----------
const state = {
  startedAt: Date.now(),
  scanning: false,
  lastScanAt: null,
  nextScanAt: Date.now() + 3000, // 啟動 3 秒後第一次掃描
  scanCountToday: 0,
  scanDate: taipeiDateStr(),
  totalSignals: 0,
  activity: [],                  // {t, text, symbol}
  markets: {},                   // symbol -> {price, prevClose, changePct, status, updatedAt}
  openSignals: {},               // symbol -> signal（進行中，pending/active）
  history: [],                   // 最近結算/發出的訊號摘要
};

MARKETS.forEach(m => {
  state.markets[m.symbol] = {
    symbol: m.symbol, code: m.code, name: m.name, accent: m.accent, decimals: m.decimals,
    price: null, prevClose: null, changePct: null, status: 'init', updatedAt: null,
  };
});

loadPersisted();

// ---------- 工具 ----------
function taipeiDateStr(ts = Date.now()) {
  return new Date(ts).toLocaleDateString('en-CA', { timeZone: 'Asia/Taipei' }); // YYYY-MM-DD
}
function taipeiTime(ts = Date.now()) {
  return new Date(ts).toLocaleTimeString('zh-TW', {
    timeZone: 'Asia/Taipei', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit',
  });
}
function fmt(n, decimals) {
  if (n == null || Number.isNaN(n)) return '—';
  return Number(n).toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}
function logActivity(text, symbol) {
  state.activity.unshift({ t: Date.now(), text, symbol: symbol || '' });
  if (state.activity.length > MAX_LOG) state.activity.length = MAX_LOG;
}

function loadPersisted() {
  try {
    const saved = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
    if (saved.scanDate === state.scanDate) state.scanCountToday = saved.scanCountToday || 0;
    state.totalSignals = saved.totalSignals || 0;
    state.openSignals = saved.openSignals || {};
    state.history = saved.history || [];
  } catch { /* 首次執行沒有檔案，忽略 */ }
}
function persist() {
  try {
    fs.mkdirSync(path.dirname(DATA_FILE), { recursive: true });
    fs.writeFileSync(DATA_FILE, JSON.stringify({
      scanDate: state.scanDate,
      scanCountToday: state.scanCountToday,
      totalSignals: state.totalSignals,
      openSignals: state.openSignals,
      history: state.history,
    }, null, 2));
  } catch (err) {
    console.warn('狀態存檔失敗：', err.message);
  }
}

// ---------- 訊號訊息 ----------
function dirZh(dir) { return dir === 'LONG' ? '做多 LONG' : '做空 SHORT'; }
function dirEmoji(dir) { return dir === 'LONG' ? '🟢' : '🔴'; }

function signalMessage(m, s) {
  const d = m.decimals;
  return [
    `${dirEmoji(s.dir)} ARGUS 破框訊號｜${m.symbol}`,
    `方向：${dirZh(s.dir)}`,
    '━━━━━━━━━━━━',
    `進場：${fmt(s.entry, d)}（等回測破框價）`,
    `止損：${fmt(s.stop, d)}`,
    `🎯 TP1：${fmt(s.tp1, d)}  (R:R 1:${s.rr1})`,
    `🎯 TP2：${fmt(s.tp2, d)}  (R:R 1:${s.rr2})`,
    '━━━━━━━━━━━━',
    `框：${fmt(s.boxLow, d)} ~ ${fmt(s.boxHigh, d)}`,
    `確認時間：TW ${taipeiTime(s.confirmedAt)}`,
  ].join('\n');
}

function settleMessage(m, s, result, exitPrice) {
  const d = m.decimals;
  const pt = s.dir === 'LONG' ? exitPrice - s.entry : s.entry - exitPrice;
  const sign = pt >= 0 ? '+' : '';
  const head = result === 'win'
    ? `✅ 結算確認｜${m.symbol} ${s.dir}`
    : `❌ 觸及止損｜${m.symbol} ${s.dir}`;
  const tail = result === 'win' ? '獲利完成 🎉' : '停損出場，控管風險';
  return [
    head,
    `進場：${fmt(s.entry, d)}`,
    `出場：${fmt(exitPrice, d)}（${sign}${fmt(pt, d)} pt）`,
    result === 'win' ? `R:R = 1:${s.tp2Hit ? s.rr2 : s.rr1}` : `R:R = 1:${s.rr1}`,
    tail,
  ].join('\n');
}

// ---------- 訊號生命週期 ----------
// pending：已破框、等回測進場；active：已回測進場、追 TP/SL。
async function updateOpenSignal(m, candles) {
  const s = state.openSignals[m.symbol];
  if (!s) return;
  const cur = candles[candles.length - 1];
  const { h, l } = cur;

  if (s.status === 'pending') {
    // 逾時未回測 → 取消
    if (Date.now() - s.createdAt > PENDING_TIMEOUT_MS) {
      logActivity(`掛單逾時取消（未回測）`, m.symbol);
      delete state.openSignals[m.symbol];
      persist();
      return;
    }
    // 觸及進場價（回測）→ 轉為進行中
    if (l <= s.entry && s.entry <= h) {
      s.status = 'active';
      s.filledAt = Date.now();
      logActivity(`已回測進場 ${fmt(s.entry, m.decimals)}`, m.symbol);
      persist();
    }
    return;
  }

  if (s.status === 'active') {
    const hitStop = s.dir === 'LONG' ? l <= s.stop : h >= s.stop;
    const hitTp2 = s.dir === 'LONG' ? h >= s.tp2 : l <= s.tp2;
    const hitTp1 = s.dir === 'LONG' ? h >= s.tp1 : l <= s.tp1;

    if (hitTp1 && !s.tp1Hit) {
      s.tp1Hit = true;
      logActivity(`TP1 到達 ${fmt(s.tp1, m.decimals)}`, m.symbol);
    }
    if (hitTp2) {
      s.tp2Hit = true;
      await settle(m, s, 'win', s.tp2);
      return;
    }
    if (hitStop) {
      // TP1 已到又回落到止損：仍算小賺/保本，但這裡以觸損結算
      const result = s.tp1Hit ? 'win' : 'loss';
      await settle(m, s, result, s.tp1Hit ? s.tp1 : s.stop);
      return;
    }
  }
}

async function settle(m, s, result, exitPrice) {
  logActivity(result === 'win' ? `結算：獲利 ✅` : `結算：止損 ❌`, m.symbol);
  await notifyTelegram(settleMessage(m, s, result, exitPrice));
  state.history.unshift({
    symbol: m.symbol, dir: s.dir, result,
    entry: s.entry, exit: exitPrice, at: Date.now(),
  });
  if (state.history.length > MAX_SIGNAL_HISTORY) state.history.length = MAX_SIGNAL_HISTORY;
  delete state.openSignals[m.symbol];
  persist();
}

async function maybeNewSignal(m, candles, htf) {
  // 同商品已有進行中訊號 → 不重複發（避免像原版「多筆同商品訊號」造成混亂）
  if (state.openSignals[m.symbol]) return;

  const sig = analyze(candles, htf);
  if (!sig) return;

  // 冷卻期內不重發
  const last = state.history.find(h => h.symbol === m.symbol);
  if (last && Date.now() - last.at < COOLDOWN_MS) return;

  const signal = {
    id: `${m.symbol}-${Date.now()}`,
    symbol: m.symbol, dir: sig.dir,
    entry: sig.entry, stop: sig.stop, tp1: sig.tp1, tp2: sig.tp2,
    boxHigh: sig.boxHigh, boxLow: sig.boxLow,
    rr1: sig.rr1, rr2: sig.rr2,
    confirmedAt: sig.confirmedAt,
    status: 'pending', createdAt: Date.now(),
    tp1Hit: false, tp2Hit: false,
  };
  state.openSignals[m.symbol] = signal;
  state.totalSignals += 1;
  logActivity(`⚡ 破框訊號 ${sig.dir}（等回測）`, m.symbol);
  await notifyTelegram(signalMessage(m, signal));
  persist();
}

// ---------- 掃描一輪 ----------
async function scanMarket(m) {
  logActivity('讀取即時報價', m.symbol);
  let candles, htf;
  try {
    candles = await fetchCandles(m, '5m');
    logActivity('同步多週期資料', m.symbol);
    htf = await fetchCandles(m, '15m').catch(() => null);
  } catch (err) {
    state.markets[m.symbol].status = 'error';
    logActivity(`資料來源異常，下輪重試（${err.message}）`, m.symbol);
    return;
  }

  const cur = candles[candles.length - 1];
  const dayAgo = candles.find(c => Date.now() - c.t <= 24 * 3600 * 1000) || candles[0];
  const mk = state.markets[m.symbol];
  mk.price = cur.c;
  mk.prevClose = dayAgo.c;
  mk.changePct = dayAgo.c ? ((cur.c - dayAgo.c) / dayAgo.c) * 100 : null;
  mk.status = 'ok';
  mk.updatedAt = Date.now();

  logActivity('重算支撐壓力區', m.symbol);
  logActivity('檢查訊號條件', m.symbol);

  await updateOpenSignal(m, candles); // 先顧進行中的單
  await maybeNewSignal(m, candles, htf);
}

async function scanCycle() {
  if (state.scanning) return;
  state.scanning = true;

  // 跨日重置每日計數
  const today = taipeiDateStr();
  if (today !== state.scanDate) { state.scanDate = today; state.scanCountToday = 0; }

  logActivity('▶ 開始掃描週期');
  for (const m of MARKETS) {
    try { await scanMarket(m); }
    catch (err) { logActivity(`掃描錯誤：${err.message}`, m.symbol); }
  }

  state.lastScanAt = Date.now();
  state.nextScanAt = Date.now() + SCAN_INTERVAL_MS;
  state.scanCountToday += 1;
  logActivity('■ 掃描完成，等待下次觸發');
  persist();
  state.scanning = false;
}

// ---------- 對外狀態（給儀表板） ----------
function snapshot() {
  return {
    engine: 'ARGUS 阿古斯',
    version: 'v1.0',
    live: true,
    startedAt: state.startedAt,
    now: Date.now(),
    lastScanAt: state.lastScanAt,
    nextScanAt: state.nextScanAt,
    scanIntervalMin: SCAN_INTERVAL_MS / 60000,
    scanCountToday: state.scanCountToday,
    totalSignals: state.totalSignals,
    scanning: state.scanning,
    markets: MARKETS.map(m => {
      const mk = state.markets[m.symbol];
      const open = state.openSignals[m.symbol] || null;
      return {
        symbol: mk.symbol, code: mk.code, name: mk.name, accent: mk.accent,
        price: mk.price == null ? null : fmt(mk.price, mk.decimals),
        changePct: mk.changePct,
        status: mk.status,
        signal: open ? { dir: open.dir, status: open.status } : null,
      };
    }),
    activity: state.activity.slice(0, 40),
    openCount: Object.keys(state.openSignals).length,
    history: state.history.slice(0, 8).map(h => ({
      symbol: h.symbol, dir: h.dir, result: h.result, at: h.at,
    })),
  };
}

// ---------- HTTP 伺服器 ----------
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8' };
const PUBLIC = path.join(__dirname, 'public');

const server = http.createServer((req, res) => {
  const url = req.url.split('?')[0];

  if (url === '/api/state') {
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' });
    res.end(JSON.stringify(snapshot()));
    return;
  }

  const filePath = url === '/' ? 'index.html' : url.replace(/^\/+/, '');
  const full = path.join(PUBLIC, filePath);
  if (!full.startsWith(PUBLIC)) { res.writeHead(403); res.end('Forbidden'); return; }
  fs.readFile(full, (err, buf) => {
    if (err) { res.writeHead(404); res.end('Not found'); return; }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(full)] || 'application/octet-stream' });
    res.end(buf);
  });
});

function start() {
  server.listen(PORT, () => {
    console.log(`\n🛰  ARGUS 阿古斯 訊號引擎已啟動`);
    console.log(`   儀表板： http://localhost:${PORT}`);
    console.log(`   掃描週期：每 ${SCAN_INTERVAL_MS / 60000} 分鐘 · 監控 ${MARKETS.map(m => m.symbol).join(' / ')}\n`);
  });
  // 排程：每 SCAN_INTERVAL 掃一次，啟動後 3 秒先掃第一輪
  setTimeout(function loop() {
    scanCycle().finally(() => setTimeout(loop, SCAN_INTERVAL_MS));
  }, 3000);
}

// 直接 `node server.js` 才啟動伺服器；被 require（測試）時只匯出函式。
if (require.main === module) start();

module.exports = { state, scanCycle, snapshot, updateOpenSignal, maybeNewSignal }; // 供測試
