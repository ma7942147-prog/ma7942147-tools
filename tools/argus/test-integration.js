// 端到端整合測試（不碰真網路）：mock 掉 global.fetch，餵合成 K 棒，
// 驗證「破框→發訊(pending)→回測進場(active)→觸及 TP2 結算(win)」整條流程。
const assert = require('assert');
const fs = require('fs');
const path = require('path');

process.env.ARGUS_TG_MUTE = '1';        // 不真的送 Telegram
process.env.PORT = '0';                  // 不占用固定埠
const DATA = path.join(__dirname, 'data', 'state.json');
try { fs.unlinkSync(DATA); } catch {}    // 從乾淨狀態開始

// --- 合成資料 ---
let phase = 1; // 1:破框上緣  2:回測  3:觸及TP2
function box(lastCandle, n = 100) {
  const rows = [];
  let t = Date.now() - (n + 2) * 300000;
  for (let i = 0; i < n - 1; i++) rows.push({ t: t += 300000, o: 100, h: 101, l: 99, c: 100 });
  rows.push({ t: t + 300000, ...lastCandle });
  return rows;
}
function toBinance(candles) { // markets.js 讀 r[0],r[1..4]
  return candles.map(c => [c.t, String(c.o), String(c.h), String(c.l), String(c.c), '0']);
}
function toYahoo(candles) {
  return { chart: { result: [{
    timestamp: candles.map(c => Math.floor(c.t / 1000)),
    indicators: { quote: [{ open: candles.map(c => c.o), high: candles.map(c => c.h), low: candles.map(c => c.l), close: candles.map(c => c.c) }] },
  }] } };
}
const risingHtf = Array.from({ length: 30 }, (_, i) => ({ t: Date.now() - (30 - i) * 900000, o: 90 + i, h: 91 + i, l: 89 + i, c: 90 + i }));
const flat = box({ o: 100, h: 101, l: 99, c: 100 });

global.fetch = async (url) => {
  const u = String(url);
  let candles;
  if (u.includes('binance')) {
    const is15 = u.includes('interval=15m');
    if (is15) candles = risingHtf;                                   // 順勢向上
    else if (phase === 1) candles = box({ o: 100, h: 105, l: 100, c: 105 }); // 向上破框
    else if (phase === 2) candles = box({ o: 100, h: 102, l: 100.5, c: 101 }); // 回測進場價 101
    else candles = box({ o: 105, h: 106, l: 104, c: 105.5 });        // 觸及 TP2 (105.4)
    return { ok: true, json: async () => toBinance(candles) };
  }
  // XAU (yahoo)：永遠盤整，不產生訊號
  return { ok: true, json: async () => toYahoo(flat) };
};

(async () => {
  const argus = require('./server');
  const { state, scanCycle } = argus;

  await scanCycle(); // 第 1 輪：破框 → 發訊
  const sig = state.openSignals['BTC/USD'];
  assert(sig, '第1輪應產生 BTC/USD 訊號');
  assert.strictEqual(sig.dir, 'LONG', '方向應為 LONG');
  assert.strictEqual(sig.status, 'pending', '初始狀態應為 pending（等回測）');
  assert.strictEqual(state.totalSignals, 1, '累計訊號應為 1');
  assert(!state.openSignals['XAU/USD'], 'XAU 盤整不應有訊號');
  console.log('  ✓ 破框 → 產生 LONG 訊號（pending）');

  phase = 2;
  await scanCycle(); // 第 2 輪：回測進場價 → active
  assert.strictEqual(state.openSignals['BTC/USD'].status, 'active', '回測後應為 active');
  console.log('  ✓ 回測進場價 → 轉為 active');

  phase = 3;
  await scanCycle(); // 第 3 輪：觸及 TP2 → 結算 win
  assert(!state.openSignals['BTC/USD'], '結算後不應再有進行中訊號');
  const h = state.history.find(x => x.symbol === 'BTC/USD');
  assert(h && h.result === 'win', '應留下一筆獲利結算');
  console.log('  ✓ 觸及 TP2 → 結算為獲利，並清掉進行中訊號');

  try { fs.unlinkSync(DATA); } catch {}
  console.log('\n整合測試全部通過 ✅');
  process.exit(0);
})().catch(e => { console.error('整合測試失敗：', e); process.exit(1); });
