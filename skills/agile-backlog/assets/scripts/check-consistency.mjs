#!/usr/bin/env node
// check-consistency.mjs —— agile-backlog 双文件一致性校验
//
// 对 agile-docs/PRODUCT-BACKLOG.md(阶段表) + agile-docs/PRODUCT-BACKLOG.yaml:
//   ① id 集合一致(.md 表格行 = .yaml items, 无遗漏/多余)
//   ② 条目数一致
//   ③ 同 id 的 priority 一致
//   ④ 同 id 的 status 一致
//   ⑤ 同 id 的 adr_refs 一致(.md 关联列 vs .yaml adr_refs)
//   ⑥ 同 id 的 point 一致(.md 点列 vs .yaml 不存 point 时跳过)
//
// 口径同 references/backlog-rules.md §七 一致性校验。
//
// 零外部依赖:内置 node:fs + node:path + 自带 lib/yaml-mini.mjs(共用最小 YAML 解析器)。
// 消费侧 npm 网络不通也能跑。
//
// 用法:
//   node assets/scripts/check-consistency.mjs                    # 报告模式,有差异显示但 exit 0
//   node assets/scripts/check-consistency.mjs --strict           # 阻塞模式,有差异 exit 1
//   node assets/scripts/check-consistency.mjs --json             # 输出 JSON
//   node assets/scripts/check-consistency.mjs --md <p> --yaml <p># 显式指定
//
// 默认:报告模式(适合 CI/hook,即使有差异也不阻塞)。--strict 用于提交前强校验。

import { readFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { yamlParse } from './lib/yaml-mini.mjs';

// ── CLI 参数 ────────────────────────────────────────────────
const args = process.argv.slice(2);
const asJson = args.includes('--json');
const strict = args.includes('--strict');
function argVal(name, fallback) {
  const i = args.indexOf(name);
  return i >= 0 && i + 1 < args.length ? args[i + 1] : fallback;
}
const ROOT = resolve(argVal('--root', process.cwd()));
const mdPath = argVal('--md', null) || join(ROOT, 'agile-docs', 'PRODUCT-BACKLOG.md');
const yamlPath = argVal('--yaml', null) || join(ROOT, 'agile-docs', 'PRODUCT-BACKLOG.yaml');

if (!existsSync(mdPath)) { console.error(`✗ 找不到 ${mdPath}`); process.exit(2); }
if (!existsSync(yamlPath)) { console.error(`✗ 找不到 ${yamlPath}`); process.exit(2); }

// ── 解析 markdown 阶段表 ────────────────────────────────────
function parseMdTable(text) {
  const lines = text.split(/\r?\n/);
  const rows = [];
  let header = null;
  const SEP = /^\|[\s:|-]+\|$/;
  const HEADER_FIRST = /^(id|编号|标题|名称|type|类型|repo|仓库|point|点数|priority|优先级|status|状态|关联|adr|来源)/i;
  for (const line of lines) {
    const t = line.trim();
    if (!t.startsWith('|')) continue;
    if (SEP.test(t)) continue;
    const cells = t.split('|').slice(1, -1).map(s => s.trim());
    if (header === null || HEADER_FIRST.test(cells[0])) {
      header = cells;
      continue;
    }
    const row = {};
    for (let i = 0; i < header.length; i++) row[header[i]] = cells[i] ?? '';
    rows.push(row);
  }
  return rows;
}

const COL = {
  id: /^(id|编号)$/i,
  point: /^(点|point|points|点数)$/i,
  priority: /^(优先级|priority)$/i,
  status: /^(状态|status)$/i,
  refs: /^(关联|关联条目|关联adr|refs|adr)$/i,
};

function mapCols(row) {
  const out = {};
  for (const [k, re] of Object.entries(COL)) {
    const key = Object.keys(row).find(c => re.test(c));
    out[k] = key ? row[key] : '';
  }
  return out;
}

// ── 解析双方 ─────────────────────────────────────────────
const mdRows = parseMdTable(readFileSync(mdPath, 'utf8'));
const yamlData = yamlParse(readFileSync(yamlPath, 'utf8'));
if (!yamlData || !Array.isArray(yamlData.items)) {
  console.error(`✗ ${yamlPath} 缺 items[]`); process.exit(2);
}
const yamlById = new Map(yamlData.items.filter(i => i.id).map(i => [i.id, i]));

const mdById = new Map();
for (const r of mdRows) {
  const m = mapCols(r);
  if (!m.id) continue;
  if (!mdById.has(m.id)) mdById.set(m.id, m);
}

// ── 6 项校验 ─────────────────────────────────────────────
const diffs = [];
function add(check, id, msg) { diffs.push({ check, id, msg }); }

// ① id 集合一致
const mdIds = new Set(mdById.keys());
const yamlIds = new Set(yamlById.keys());
for (const id of mdIds) if (!yamlIds.has(id)) add('id 集合', id, `在 .md 但不在 .yaml`);
for (const id of yamlIds) if (!mdIds.has(id)) add('id 集合', id, `在 .yaml 但不在 .md`);

// ② 条目数一致(派生自 ①,差异数若非零即数量不一致)
if (mdById.size !== yamlById.size) add('条目数', '*', `md=${mdById.size} vs yaml=${yamlById.size}`);

// ③④⑤⑥ 仅对两侧都有的 id 比对
for (const id of mdIds) {
  if (!yamlById.has(id)) continue;
  const m = mdById.get(id);
  const y = yamlById.get(id);

  // ③ priority
  const mp = (m.priority || '').trim();
  const yp = (y.priority || '').trim();
  if (mp && yp && mp !== yp) add('priority', id, `md="${mp}" vs yaml="${yp}"`);

  // ④ status — md/yaml 是契约同义:md 人类用语 ↔ yaml schema 枚举
  const msRaw = (m.status || '').trim();
  const ysRaw = (y.status || '').trim();
  const statusAlias = { '待办': '待办', '已完成': '已完成', '已撤回': 'withdrawn' };
  const ms = statusAlias[msRaw] || msRaw;
  const ys = ysRaw;
  if (ms && ys && ms !== ys) add('status', id, `md="${msRaw}" vs yaml="${ysRaw}"`);

  // ⑤ adr_refs(.md 关联列可混条目 id 与 ADR id,仅比对 ADR 编号 ADR-NNN;
  //    占位符 —/-/无 跳过;yaml 直接是数组)
  const mdRefsRaw = (m.refs || '').split(/[\/,，\s]+/).map(s => s.trim()).filter(s => s && s !== '—' && s !== '-' && s !== '无');
  const mdAdrRefs = mdRefsRaw.filter(r => /^ADR[-]?\d+$/i.test(r));
  const yRefs = y.adr_refs || [];
  const mdSet = new Set(mdAdrRefs.map(r => r.toUpperCase())), ySet = new Set(yRefs.map(r => r.toUpperCase()));
  for (const r of mdSet) if (!ySet.has(r)) add('adr_refs', id, `.md 含 ${r} 但 .yaml 无`);
  for (const r of ySet) if (!mdSet.has(r)) add('adr_refs', id, `.yaml 含 ${r} 但 .md 无`);

  // ⑥ point(yaml 不存 point 时跳过;md 有数字时校验)
  const mpNum = Number(m.point);
  if (Number.isFinite(mpNum) && mpNum > 0 && y.point != null && Number(y.point) !== mpNum) {
    add('point', id, `md=${mpNum} vs yaml=${y.point}`);
  }
}

// ── 输出 ────────────────────────────────────────────────
const passed = diffs.length === 0;
const report = { passed, diffs, summary: {
  md_count: mdById.size, yaml_count: yamlById.size,
  diff_count: diffs.length,
}};

if (asJson) {
  console.log(JSON.stringify(report, null, 2));
} else {
  console.log('## Backlog 双文件一致性校验\n');
  console.log(`.md 条目数: ${mdById.size}`);
  console.log(`.yaml 条目数: ${yamlById.size}\n`);

  if (passed) {
    console.log('✓ 全部通过(id 集合 / 条目数 / priority / status / adr_refs / point)');
  } else {
    console.log(`✗ 发现 ${diffs.length} 处不一致:\n`);
    const byCheck = {};
    for (const d of diffs) (byCheck[d.check] ||= []).push(d);
    for (const [check, list] of Object.entries(byCheck)) {
      console.log(`### ${check}`);
      for (const d of list) console.log(`- ${d.id}: ${d.msg}`);
      console.log('');
    }
    console.log('修复后重跑直到 0 处不一致。优先级 / status 漂移最常见,先看这两类。');
  }
}

process.exit(strict && !passed ? 1 : 0);
