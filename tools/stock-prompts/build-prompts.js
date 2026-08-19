#!/usr/bin/env node
/**
 * 從 obsidian/*.md 抽出「提示詞本體」與 frontmatter，產生機器可讀的 prompts.json。
 * 單一事實來源是 markdown 筆記，避免筆記跟 JSON 各改各的而漂移。
 */
const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, 'obsidian');
const OUT = path.join(__dirname, 'prompts.json');

function parseFrontmatter(lines) {
  if (lines[0] !== '---') return {};
  const end = lines.indexOf('---', 1);
  if (end < 0) return {};
  const fm = {};
  let key = null;
  for (const line of lines.slice(1, end)) {
    const listItem = line.match(/^\s+-\s+(.*)$/);
    if (listItem && key) {
      fm[key] = Array.isArray(fm[key]) ? fm[key] : [];
      fm[key].push(listItem[1].trim());
      continue;
    }
    const kv = line.match(/^(\w+):\s*(.*)$/);
    if (kv) {
      key = kv[1];
      fm[key] = kv[2].trim();
    }
  }
  return fm;
}

/**
 * 抓出檔案裡所有 ```text 區塊並接起來。
 * 筆記把「主提示詞」和「想存檔才加的 JSON 附加段」分成兩塊給人看，
 * 但程式化使用時兩塊都要，因為 JSON 輸出才是可比對的部分。
 */
function extractPrompt(lines) {
  const blocks = [];
  let body = null;
  let inner = false;
  for (const line of lines) {
    if (body === null) {
      if (line.trim() === '```text') body = [];
      continue;
    }
    if (line.trimEnd() === '```' && !inner) {
      blocks.push(body.join('\n'));
      body = null;
      continue;
    }
    if (line.startsWith('```')) inner = !inner;
    body.push(line);
  }
  return blocks.length ? blocks.join('\n\n') : null;
}

const prompts = [];
for (const file of fs.readdirSync(SRC).sort()) {
  if (!file.endsWith('.md')) continue;
  const lines = fs.readFileSync(path.join(SRC, file), 'utf8').split('\n');
  const fm = parseFrontmatter(lines);
  if (fm.type !== 'prompt') continue;
  const template = extractPrompt(lines);
  if (!template) {
    console.error(`⚠️  ${file}: 找不到 \`\`\`text 提示詞區塊，略過`);
    continue;
  }
  prompts.push({
    id: fm.step,
    name: fm.step_name,
    cadence: fm.cadence,
    triggers: fm.triggers || [],
    variables: fm.variables || [],
    note: file,
    template,
  });
}

const pack = {
  system: '美股研究系統 — Jenny 八步驟',
  version: '1.0.0',
  generated_at: new Date().toISOString().slice(0, 10),
  cadence_map: {
    daily: ['DAILY'],
    weekly: ['WEEKLY', 'S1'],
    monthly: ['S2', 'MONTHLY_QUARTERLY'],
    quarterly: ['S4', 'S5', 'S6', 'S7', 'S8'],
    event: ['S3'],
  },
  prompts,
};

fs.writeFileSync(OUT, JSON.stringify(pack, null, 2) + '\n');
console.log(`✅ ${prompts.length} 個提示詞 → ${path.relative(process.cwd(), OUT)}`);
for (const p of prompts) console.log(`   ${p.id.padEnd(20)} ${p.cadence.padEnd(10)} ${p.name}`);
