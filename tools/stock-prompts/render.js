#!/usr/bin/env node
/**
 * 把提示詞模板的 {{VAR}} 換成實際值，直接輸出可貼進 AI 的完整提示詞。
 *
 *   node render.js S1
 *   node render.js S6 --TICKER=AVGO --THESIS="AI 網通市占持續擴大" --FINANCIALS="$(cat q3.txt)"
 *   node render.js --list
 *
 * 未指定的 {{DATE}} 會自動帶入今天。
 */
const fs = require('fs');
const path = require('path');

const pack = JSON.parse(fs.readFileSync(path.join(__dirname, 'prompts.json'), 'utf8'));
const args = process.argv.slice(2);

if (args.length === 0 || args[0] === '--list' || args[0] === '-l') {
  console.log(`${pack.system}  v${pack.version}\n`);
  console.log('ID'.padEnd(20) + 'CADENCE'.padEnd(12) + 'VARIABLES');
  console.log('-'.repeat(72));
  for (const p of pack.prompts) {
    console.log(p.id.padEnd(20) + p.cadence.padEnd(12) + (p.variables.join(', ') || '—'));
  }
  console.log('\n用法：node render.js <ID> --VAR=值 ...');
  process.exit(0);
}

const id = args[0].toUpperCase();
const prompt = pack.prompts.find((p) => p.id === id);
if (!prompt) {
  console.error(`找不到提示詞「${id}」。可用：${pack.prompts.map((p) => p.id).join(', ')}`);
  process.exit(1);
}

const vars = { DATE: new Date().toISOString().slice(0, 10) };
for (const arg of args.slice(1)) {
  const m = arg.match(/^--([A-Z_]+)=([\s\S]*)$/);
  if (!m) {
    console.error(`參數格式錯誤：${arg}（應為 --VAR=值）`);
    process.exit(1);
  }
  vars[m[1]] = m[2];
}

const missing = prompt.variables.filter((v) => !(v in vars));
if (missing.length) {
  console.error(`⚠️  缺少變數：${missing.map((v) => '--' + v).join(' ')}`);
  process.exit(1);
}

const rendered = prompt.template.replace(/\{\{(\w+)\}\}/g, (whole, name) =>
  name in vars ? vars[name] : whole
);

const leftover = rendered.match(/\{\{\w+\}\}/g);
if (leftover) console.error(`⚠️  未替換的變數：${[...new Set(leftover)].join(', ')}\n`);

process.stdout.write(rendered + '\n');
