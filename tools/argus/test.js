// 破框策略離線測試（不碰網路）：造幾組 K 棒，驗證多空破框、假突破過濾、順勢過濾。
const assert = require('assert');
const { analyze } = require('./strategy');

// 造一段在 100±1 之間盤整的 20 根框，最後 1 根收在 breakClose。
function build(breakClose, { boxMid = 100, boxHalf = 1 } = {}) {
  const c = [];
  let t = Date.now() - 30 * 5 * 60000;
  for (let i = 0; i < 21; i++) {
    const o = boxMid, cl = boxMid;
    c.push({ t: t += 300000, o, h: boxMid + boxHalf, l: boxMid - boxHalf, c: cl });
  }
  c.push({ t: t += 300000, o: boxMid, h: Math.max(boxMid, breakClose), l: Math.min(boxMid, breakClose), c: breakClose });
  return c;
}
// 明確上升的高週期趨勢
const upHtf = Array.from({ length: 30 }, (_, i) => ({ t: i, o: 90 + i, h: 91 + i, l: 89 + i, c: 90 + i }));
const downHtf = Array.from({ length: 30 }, (_, i) => ({ t: i, o: 120 - i, h: 121 - i, l: 119 - i, c: 120 - i }));

let pass = 0;
function ok(name, cond) { assert(cond, name); console.log('  ✓', name); pass++; }

// 1. 向上破框 + 順勢(up) → LONG
const s1 = analyze(build(103), upHtf);
ok('向上大幅破框 → 產生 LONG', s1 && s1.dir === 'LONG');
ok('LONG 進場=框頂', s1 && s1.entry === 101);
ok('LONG 止損在框底之下', s1 && s1.stop < 99);
ok('TP2 比 TP1 遠', s1 && Math.abs(s1.tp2 - s1.entry) > Math.abs(s1.tp1 - s1.entry));

// 2. 向下破框 + 順勢(down) → SHORT
const s2 = analyze(build(97), downHtf);
ok('向下大幅破框 → 產生 SHORT', s2 && s2.dir === 'SHORT');
ok('SHORT 止損在框頂之上', s2 && s2.stop > 101);

// 3. 沒破框（收在框內）→ 無訊號
ok('框內收盤 → 無訊號', analyze(build(100), upHtf) === null);

// 4. 假突破（只超出一點點）→ 被過濾
ok('微幅突破 → 被濾掉', analyze(build(101.01), upHtf) === null);

// 5. 逆勢破框（向上破但高週期向下）→ 被順勢過濾擋掉
ok('逆勢破框 → 被擋', analyze(build(103), downHtf) === null);

console.log(`\n全部 ${pass} 項通過 ✅`);
