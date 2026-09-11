#!/usr/bin/env node
// inventory.mjs —— agile-backlog 盘点脚本（统计快照）
//
// 解析 agile-docs/PRODUCT-BACKLOG.md（阶段表）+ agile-docs/PRODUCT-BACKLOG.yaml，
// 输出条目数 / 总点数 / 按优先级分组 / 按状态分组 / 按类型分组 / ADR 关联覆盖率。
//
// 用途: 取代"增量手算漂移"——每次改动后必跑,覆盖式统计而非人工加减。
//
// 用法:
//   node assets/scripts/inventory.mjs                                  # 自动找 agile-docs/
//   node assets/scripts/inventory.mjs --md <path> --yaml <path>        # 显式指定
//   node assets/scripts/inventory.mjs --json                           # 输出 JSON
//
// 退出码: 0 = 成功; 非零表示解析失败(不是校验失败)。

import { readFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import yaml from 'js-yaml';

// ── CLI 参数 ────────────────────────────────────────────────
const args = process.argv.slice(2);
const asJson = args.includes('--json');
function argVal(name, fallback) {
  const i = args.indexOf(name);
  return i >= 0 && i + 1 < args.length ? args[i + 1] : fallback;
}
const ROOT = resolve(argVal('--root', process.cwd()));
const MD_PATH = argVal('--md', null);
const YAML_PATH = argVal('--yaml', null);

const mdPath = MD_PATH || join(ROOT, 'agile-docs', 'PRODUCT-BACKLOG.md');
const yamlPath = YAML_PATH || join(ROOT, 'agile-docs', 'PRODUCT-BACKLOG.yaml');

if (!existsSync(mdPath)) {
  console.error(`✗ 找不到 ${mdPath}`);
  process.exit(2);
}
if (!existsSync(yamlPath)) {
  console.error(`✗ 找不到 ${yamlPath}`);
  process.exit(2);
}

// ── 解析 markdown 阶段表 ────────────────────────────────────
// 解析整个 md 文件的所有 backlog 表格行:遇到 | 开头的行视为表格候选,
// 跳过表头分隔行(|---|),其余 | 行按列名映射到字段。
// 多张表(「阶段 N」分块)支持:若新一行 cell[0] 匹配已知字段名,视为新表表头重置 header。
function parseMdTable(text) {
  const lines = text.split(/\r?\n/);
  const rows = [];
  let header = null;
  const SEP = /^\|[\s:|-]+\|$/;
  // 第一格匹配已知列名前缀 → 视为表头
  const HEADER_FIRST = /^(id|编号|标题|名称|type|类型|repo|仓库|point|点数|priority|优先级|status|状态|关联|adr|来源)/i;
  for (const line of lines) {
    const t = line.trim();
    if (!t.startsWith('|')) continue;
    if (SEP.test(t)) continue;  // 表头分隔行,不影响 header
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

// 列名 → 字段映射(兼容「ID/id/编号」等常见命名变体;取首匹配)
const COL = {
  id: /^(id|编号)$/i,
  title: /^(标题|名称|name|title)$/i,
  type: /^(类型|type)$/i,
  repo: /^(仓库|repo|repository)$/i,
  point: /^(点|point|points|点数)$/i,
  priority: /^(优先级|priority)$/i,
  status: /^(状态|status)$/i,
  refs: /^(关联|关联条目|关联adr|refs|adr)$/i,
  source: /^(来源|来源\/依据|source来源|source)$/i,
};

function mapCols(row) {
  const out = {};
  for (const [k, re] of Object.entries(COL)) {
    const key = Object.keys(row).find(c => re.test(c));
    out[k] = key ? row[key] : '';
  }
  return out;
}

// ── 解析 yaml ───────────────────────────────────────────────
const yamlData = yaml.load(readFileSync(yamlPath, 'utf8'));
if (!yamlData || !Array.isArray(yamlData.items)) {
  console.error(`✗ ${yamlPath} 缺 items[] 或格式错误`);
  process.exit(2);
}
const yamlById = new Map();
for (const it of yamlData.items) {
  if (it.id) yamlById.set(it.id, it);
}

// ── 解析 md + 联合 ────────────────────────────────────
const mdRows = parseMdTable(readFileSync(mdPath, 'utf8'));
const items = [];
const seenMd = new Set();
for (const r of mdRows) {
  const m = mapCols(r);
  if (!m.id) continue;
  seenMd.add(m.id);
  const y = yamlById.get(m.id) || {};
  items.push({
    id: m.id,
    title: m.title || '',
    type: m.type || '',
    repo: m.repo || '',
    point: Number(m.point) || 0,
    priority: (m.priority || y.priority || '').trim(),
    status: (m.status || y.status || '').trim(),
    refs: m.refs || '',
    adr_refs: y.adr_refs || [],
    confirmed: y.confirmed !== false,
    withdrawn: y.withdrawn === true || y.status === '已撤回',
  });
}

// yaml 里有但 md 没收录的条目(异常数据,纳入统计并标记)
for (const [id, y] of yamlById) {
  if (!seenMd.has(id)) {
    items.push({
      id, title: '', type: '', repo: '', point: 0,
      priority: y.priority || '', status: y.status || '',
      refs: '', adr_refs: y.adr_refs || [],
      confirmed: y.confirmed !== false,
      withdrawn: y.withdrawn === true || y.status === '已撤回',
    });
  }
}

// ── 聚合 ────────────────────────────────────────────────
const PRIORITIES = ['Must', 'Should', 'Could', "Won't"];
const STATUSES = ['待办', '已完成', '已撤回'];
const TYPES = ['技术', '功能'];

function bucket(field, keys) {
  const out = {};
  for (const k of keys) out[k] = { count: 0, points: 0 };
  out.__other__ = { count: 0, points: 0 };
  for (const it of items) {
    const k = it[field] || '__other__';
    if (!out[k]) out[k] = { count: 0, points: 0 };
    out[k].count += 1;
    out[k].points += it.point;
  }
  return out;
}

const totalCount = items.length;
const totalPoints = items.reduce((s, it) => s + it.point, 0);
const activeItems = items.filter(it => !it.withdrawn);
const activeCount = activeItems.length;
const activePoints = activeItems.reduce((s, it) => s + it.point, 0);
const adrCovered = activeItems.filter(it => it.adr_refs.length > 0 || it.refs).length;
const unconfirmedActive = activeItems.filter(it => it.status === '待办' && !it.confirmed).length;

const byPriority = bucket('priority', PRIORITIES);
const byStatus = bucket('status', STATUSES);
const byType = bucket('type', TYPES);

// ── 输出 ────────────────────────────────────────────────
const report = {
  total: { count: totalCount, points: totalPoints },
  active: {
    count: activeCount, points: activePoints,
    note: '排除已撤回条目,等于"参与排序的有效条目"',
  },
  by_priority: byPriority,
  by_status: byStatus,
  by_type: byType,
  adr_coverage: {
    covered: adrCovered,
    total_active: activeCount,
    rate: activeCount > 0 ? Math.round((adrCovered / activeCount) * 100) : 0,
  },
  unconfirmed_active: unconfirmedActive,
};

if (asJson) {
  console.log(JSON.stringify(report, null, 2));
} else {
  const pad = (s, n) => String(s).padEnd(n);
  console.log('## Backlog 盘点快照\n');
  console.log(`**总条目**    ${totalCount} 条 / ${totalPoints} 点`);
  console.log(`**有效条目**(排除已撤回)  ${activeCount} 条 / ${activePoints} 点\n`);

  console.log('### 按优先级');
  for (const p of PRIORITIES) {
    const b = byPriority[p];
    if (b.count > 0) console.log(`- ${pad(p, 8)} ${b.count} 条 / ${b.points} 点`);
  }
  const otherP = byPriority.__other__;
  if (otherP.count > 0) console.log(`- ${pad('(其它)', 8)} ${otherP.count} 条 / ${otherP.points} 点`);

  console.log('\n### 按状态');
  for (const s of STATUSES) {
    const b = byStatus[s];
    if (b.count > 0) console.log(`- ${pad(s, 8)} ${b.count} 条 / ${b.points} 点`);
  }
  const otherS = byStatus.__other__;
  if (otherS.count > 0) console.log(`- ${pad('(其它)', 8)} ${otherS.count} 条 / ${otherS.points} 点`);

  console.log('\n### 按类型');
  for (const t of TYPES) {
    const b = byType[t];
    if (b.count > 0) console.log(`- ${pad(t, 8)} ${b.count} 条 / ${b.points} 点`);
  }

  console.log(`\n### ADR 关联覆盖`);
  console.log(`- ${adrCovered} / ${activeCount} (${report.adr_coverage.rate}%) 有效条目有关联 ADR`);

  if (unconfirmedActive > 0) {
    console.log(`\n⚠ **未确认条目**: ${unconfirmedActive} 条状态为「待办」且 confirmed=false——Sprint 取用前需显式确认`);
  }
}