#!/usr/bin/env node
// 校验 references 内交叉引用的可达性：`文件` §N / `文件.md` §N.M / 裸 §N
//
// 用法:
//   node scripts/check-refs.mjs               # 扫描 skills/*/references/，只报告不阻断
//   node scripts/check-refs.mjs --strict      # 全量扫描且悬空即退出 1
//   node scripts/check-refs.mjs <目录...>      # 只查指定目录（默认严格，悬空即退出 1）
//   node scripts/check-refs.mjs -v            # 同时打印每处引用的实际标题（人工核对语义是否错位）
//
// 退出码: 0 全部可达（或全量模式下仅报告） / 1 存在悬空引用
//
// 为什么需要 -v：章节编号可解析不代表语义正确。删减章节后重编号会复用旧编号，
// 此时 §5 依然"可达"，但指向的是另一个标题——纯可达性校验抓不到这种错位。
//
// 为什么要区分全量/单目录的严格度：各 skill 的标题风格不统一（`## 1. 标题`、
// `## §1 标题`、`## 一、标题` 都有），全量扫描难免残留噪音，拿去当 pre-commit
// 门禁会拦住一切提交；单目录（改完某个 skill 后自查）才是可信场景。
import { readdirSync, readFileSync, existsSync, statSync } from 'node:fs';
import { join, resolve, dirname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const VERBOSE = process.argv.includes('-v');
const STRICT = process.argv.includes('--strict');
const given = process.argv.slice(2).filter((a) => !a.startsWith('-'));

// 单目录默认严格；全量默认只报告
const strictMode = STRICT || given.length > 0;

const dirs = given.length > 0 ? given.map((d) => resolve(d)) : discover();
if (dirs.length === 0) {
  console.error('✗ 没有找到任何 references 目录（skills/*/references/）');
  process.exit(1);
}

function discover() {
  const skillsRoot = join(ROOT, 'skills');
  if (!existsSync(skillsRoot)) return [];
  return readdirSync(skillsRoot, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => join(skillsRoot, d.name, 'references'))
    .filter((p) => existsSync(p) && statSync(p).isDirectory());
}

// ── 标题解析 ────────────────────────────────────────────────────────────────
// 章节标题四种写法都在仓库里出现过：
//   `## 1. 标题` / `## §1 标题` / `### 1.1 标题` / `## 一、标题`
const RE_HEAD_ARABIC = /^#{2,3}\s+§?\s*(\d+(?:\.\d+)?)[.、．]?\s*(.*)$/;
const RE_HEAD_CN = /^#{2,3}\s+([一二三四五六七八九十]{1,3})[、.．]?\s*(.*)$/;
const CN_DIGIT = '零一二三四五六七八九';

function cnToNum(s) {
  if (s.length === 1) {
    const i = CN_DIGIT.indexOf(s);
    return i > 0 ? String(i) : null;
  }
  if (s === '十') return '10';
  if (s[0] === '十') {
    const i = CN_DIGIT.indexOf(s[1]);
    return i > 0 ? `1${i}` : null; // 十一 → 11
  }
  const ti = s.indexOf('十');
  if (ti === 1) {
    const a = CN_DIGIT.indexOf(s[0]);
    if (a <= 0) return null;
    const rest = s.slice(2);
    if (!rest) return String(a * 10); // 二十 → 20
    const b = CN_DIGIT.indexOf(rest);
    return b > 0 ? String(a * 10 + b) : null; // 二十三 → 23
  }
  return null;
}

function parseHeading(line) {
  let m = RE_HEAD_ARABIC.exec(line);
  if (m) return [m[1], m[2].trim()];
  m = RE_HEAD_CN.exec(line);
  if (m) {
    const n = cnToNum(m[1]);
    if (n) return [n, m[2].trim()];
  }
  return null;
}

// ── 引用模式 ────────────────────────────────────────────────────────────────
// 写法兼容（都真实存在于仓库）：`11-transaction.md §3` / `03` §2（简写）/ `SKILL.md §6`
//   / `03-serialization.md §3-§4` / `10-antipattern.md §1、§10、§11`（一个文件挂多个 §）
const SECTAIL = '(?:\\s*[、,，\\-–~]\\s*§\\s*\\d+(?:\\.\\d+)?)*';
const RE_CROSS_QUOTED = new RegExp('`([\\w-]+(?:\\.md)?)`\\s*§\\s*(\\d+(?:\\.\\d+)?)' + SECTAIL, 'g');
const RE_CROSS_PLAIN = new RegExp('(?<![`\\w-])([\\w-]+\\.md)\\s*§\\s*(\\d+(?:\\.\\d+)?)' + SECTAIL, 'g');
// 裸 §N 视为引用本文件；但 `skill-name §6` 这种（引用别的 skill 的 SKILL.md）不算
const RE_LOCAL = /(?<![\w-]+\s)(?<![\w`.])(?:见\s*)?§\s*(\d+(?:\.\d+)?)/g;

let totalBad = 0;
let totalFiles = 0;
let totalSecs = 0;

for (const dir of dirs) {
  if (!existsSync(dir)) {
    console.log(`✗ 目录不存在: ${dir}`);
    totalBad++;
    continue;
  }

  const files = readdirSync(dir).filter((f) => f.endsWith('.md'));
  if (files.length === 0) continue;

  // 多 skill 扫描时用 skill 名做前缀，否则单目录只报文件名
  const label = dirs.length > 1 ? `${basename(dirname(dir))}/` : '';

  // 建章节表：{ '11-transaction.md': Map([['3','saveBatch 与事务的关系'], ...]) }
  const outline = new Map();
  const addOutline = (name, path) => {
    const secs = new Map();
    for (const line of readFileSync(path, 'utf8').split('\n')) {
      const parsed = parseHeading(line);
      if (parsed) secs.set(parsed[0], parsed[1]);
    }
    outline.set(name, secs);
  };
  for (const f of files) addOutline(f, join(dir, f));

  // references 里会引用 `SKILL.md §N`，它在 references 的上一级
  const skillMd = join(dirname(dir), 'SKILL.md');
  if (existsSync(skillMd)) addOutline('SKILL.md', skillMd);

  // 简写文件名：`03` → `03-design-methods.md`（前缀唯一时才认，避免歧义）
  const byPrefix = new Map();
  for (const f of files) {
    const p = /^(\d+)/.exec(f);
    if (p) byPrefix.set(p[1], byPrefix.has(p[1]) ? null : f);
  }
  const resolveTarget = (name) => {
    if (outline.has(name)) return name;
    if (!name.endsWith('.md') && byPrefix.get(name)) return byPrefix.get(name);
    return null;
  };

  let bad = 0;
  for (const f of files) {
    const lines = readFileSync(join(dir, f), 'utf8').split('\n');

    lines.forEach((line, i) => {
      const at = `${label}${f}:${i + 1}`;
      let rest = line;

      const checkCross = (m) => {
        rest = rest.replace(m[0], ' ');
        const target = resolveTarget(m[1]);
        // 一个引用串里可能挂多个 §（§1、§10、§11），全部核对
        const secs = [...m[0].matchAll(/§\s*(\d+(?:\.\d+)?)/g)].map((x) => x[1]);
        if (!target) {
          console.log(`✗ ${at}  目标文件不存在: ${m[1]}`);
          bad += secs.length;
          return;
        }
        for (const sec of secs) {
          const title = outline.get(target).get(sec);
          if (!title) {
            console.log(`✗ ${at}  ${target} §${sec} 不存在（该文件现有: ${[...outline.get(target).keys()].join(', ')}）`);
            bad++;
          } else if (VERBOSE) {
            console.log(`  ${at}  → ${target} §${sec}「${title}」`);
          }
        }
      };

      for (const m of line.matchAll(RE_CROSS_QUOTED)) checkCross(m);
      for (const m of rest.matchAll(RE_CROSS_PLAIN)) checkCross(m);

      // 裸 §N 视为引用本文件
      for (const m of rest.matchAll(RE_LOCAL)) {
        const sec = m[1];
        const title = outline.get(f).get(sec);
        if (!title) {
          console.log(`✗ ${at}  本文件 §${sec} 不存在`);
          bad++;
        } else if (VERBOSE) {
          console.log(`  ${at}  → 本文件 §${sec}「${title}」`);
        }
      }
    });
  }

  const secCount = [...outline.values()].reduce((a, s) => a + s.size, 0);
  totalBad += bad;
  totalFiles += files.length;
  totalSecs += secCount;

  if (dirs.length > 1) {
    console.log(`${bad === 0 ? '✓' : '✗'} ${label.replace(/\/$/, '')}  ${files.length} 文件 / ${secCount} 章节${bad === 0 ? '' : ` / ${bad} 处悬空`}`);
  }
}

console.log(`\n${totalBad === 0 ? '✓ 全部可达' : `✗ ${totalBad} 处悬空引用`}  （${totalFiles} 个文件，${totalSecs} 个章节）`);
if (totalBad > 0 && !strictMode) {
  console.log('   全量扫描仅报告、不阻断；要让它退出 1 请加 --strict 或指定目录。');
}
process.exit(totalBad > 0 && strictMode ? 1 : 0);
