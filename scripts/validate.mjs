#!/usr/bin/env node
// validate.mjs —— 技能内容静态校验(只读,不写任何文件)
//
// 校验四块:
//   ① frontmatter 规范: name 匹配目录名 / description≤1024 / version semver /
//      slug+displayName(SkillHub 发布前置) / dependencies 引用真实存在
//   ② 引用完整性: SKILL.md 与 references 里引用的 references/<file> 实际存在
//      (完整文件名,含非编号名与 .yaml);缩写式 references/NN 的 NN 前缀须有对应文件;
//      plugin-map.json 的 group 成员在 skills/ 存在且不重复映射
//   ③ references 可达性(防孤儿/防漂移,源自敏捷套件历轮评估根因):
//      孤儿 error  —— references/ 下文件在 skills/ 树内零引用(完整名或缩写,跨技能合法)
//      可达 warning —— 从本技能 SKILL.md 沿指针图走不到的自身 reference
//
// 用法:
//   node scripts/validate.mjs            # 有错误则退出码 1,否则 0
//   node scripts/validate.mjs --json     # 输出 JSON(供 CI / 工具解析)

import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join, relative, dirname, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import yaml from 'js-yaml';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const SKILLS_DIR = join(ROOT, 'skills');
const PLUGIN_MAP = join(__dirname, 'plugin-map.json');

const errors = [];
const warnings = [];

const err = (scope, msg) => errors.push(`${scope}: ${msg}`);
const warn = (scope, msg) => warnings.push(`${scope}: ${msg}`);

// ── 工具 ──────────────────────────────────────────────────

function readSkillFrontmatter(skillDir) {
  const mdPath = join(skillDir, 'SKILL.md');
  if (!existsSync(mdPath)) return { error: '缺 SKILL.md' };
  const text = readFileSync(mdPath, 'utf8');
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) return { error: 'SKILL.md 无合法 frontmatter(缺 --- 分隔)' };
  try {
    return { fm: yaml.load(m[1]) };
  } catch (e) {
    return { error: `frontmatter YAML 解析失败: ${e.message}` };
  }
}

function listContentFiles(dir) {
  const out = [];
  const walk = (d) => {
    for (const entry of readdirSync(d)) {
      if (entry.startsWith('.')) continue;
      const full = join(d, entry);
      if (statSync(full).isDirectory()) walk(full);
      else if (/\.(md|ya?ml)$/.test(entry)) out.push(full);
    }
  };
  walk(dir);
  return out;
}

// ── ① frontmatter 规范 ───────────────────────────────────

function validateFrontmatter(name) {
  const skillDir = join(SKILLS_DIR, name);
  const { fm, error } = readSkillFrontmatter(skillDir);
  if (error) { err(name, error); return; }

  // name
  if (!fm.name) err(name, '缺 name');
  else if (fm.name !== name) err(name, `name "${fm.name}" 与目录名 "${name}" 不一致`);
  else if (fm.name.length > 64) err(name, `name 超 64 字符`);
  else if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(fm.name)) err(name, 'name 含非法字符(仅小写字母/数字/连字符,无前导/尾随/连续连字符)');

  // description
  if (!fm.description) err(name, '缺 description');
  else if (String(fm.description).length > 1024) err(name, `description 超 1024 字符(当前 ${String(fm.description).length})`);

  // version (semver)
  if (fm.version === undefined || fm.version === null) err(name, '缺 version');
  else if (!/^\d+\.\d+\.\d+/.test(String(fm.version))) err(name, `version "${fm.version}" 非 semver(x.y.z)`);

  // slug + displayName(SkillHub 发布前置)
  if (!fm.slug) err(name, '缺 slug(SkillHub 发布前置)');
  if (!fm.displayName) err(name, '缺 displayName(SkillHub 发布前置)');

  // dependencies 引用真实存在的技能
  if (fm.dependencies) {
    if (!Array.isArray(fm.dependencies)) { err(name, 'dependencies 应为数组'); return; }
    for (const dep of fm.dependencies) {
      const depName = dep?.skill;
      if (!depName) { err(name, 'dependencies 项缺 skill 字段'); continue; }
      if (!existsSync(join(SKILLS_DIR, depName))) err(name, `dependencies 引用不存在的技能 "${depName}"`);
    }
  }
}

// ── ② 引用完整性 ─────────────────────────────────────────

// 全局收集所有技能的 references 文件名(去重)——跨技能引用视为合法,仅"全局不存在"才算悬空
function collectAllRefFiles(skillDirs) {
  const all = new Set();
  for (const name of skillDirs) {
    const refDir = join(SKILLS_DIR, name, 'references');
    if (!existsSync(refDir)) continue;
    for (const f of readdirSync(refDir)) {
      if (/\.(md|ya?ml)$/.test(f)) all.add(f);
    }
  }
  return all;
}

// 完整式引用: references/<file>(编号或非编号名,.md/.yaml)
const FULL_REF = /references\/([A-Za-z0-9][A-Za-z0-9._-]*\.(?:md|ya?ml))/g;
// 缩写式引用: references/NN(后面不能再跟文件名字符——那属于完整式)
function abbrRefRegex(nn) {
  return new RegExp(`references/${nn}(?![\\w.-])`);
}

function validateReferences(name, allFiles, allRefFiles) {
  const skillDir = join(SKILLS_DIR, name);
  const ownRefDir = join(skillDir, 'references');
  const ownRefFiles = existsSync(ownRefDir)
    ? readdirSync(ownRefDir).filter(f => /\.(md|ya?ml)$/.test(f)) : [];

  for (const { path, content } of allFiles) {
    if (!path.startsWith(skillDir)) continue;
    // ① 完整式悬空
    FULL_REF.lastIndex = 0;
    let m;
    while ((m = FULL_REF.exec(content)) !== null) {
      if (!allRefFiles.has(m[1])) {
        err(name, `${relative(ROOT, path)} 引用不存在的 references/${m[1]}`);
      }
    }
    // ② 缩写式错位: references/NN 在本技能无 NN- 前缀文件
    const abbr = /references\/(\d{2})(?![\w.-])/g;
    while ((m = abbr.exec(content)) !== null) {
      if (!ownRefFiles.some(f => f.startsWith(`${m[1]}-`))) {
        err(name, `${relative(ROOT, path)} 缩写引用 references/${m[1]} 在本技能 references/ 无对应文件(编号错位?)`);
      }
    }
  }
}

// ── ③ references 可达性(孤儿 + SKILL.md 可达) ─────────────

function validateReachability(name, allFiles) {
  const refDir = join(SKILLS_DIR, name, 'references');
  if (!existsSync(refDir)) return;
  const refFiles = readdirSync(refDir).filter(f => /\.(md|ya?ml)$/.test(f));

  // 孤儿: 完整文件名在 skills/ 树内(跨技能合法)出现过,或缩写 NN 被本技能文件引用
  for (const f of refFiles) {
    const nn = f.match(/^(\d{2})-/)?.[1];
    const cited = allFiles.some(({ path, content }) => {
      if (path === join(refDir, f)) return false; // 不算自引
      if (content.includes(f)) return true;
      // 缩写只在本技能内解析(其他技能的 references/99 指向它自己的文件)
      return nn !== undefined && path.startsWith(join(SKILLS_DIR, name) + sep) && abbrRefRegex(nn).test(content);
    });
    if (!cited) {
      err(name, `references/${f} 是孤儿: skills/ 树内零引用(agent 无法发现,内容不可达)`);
    }
  }

  // SKILL.md 可达: 从 SKILL.md 沿指针图(完整式+缩写式)BFS,走不到的自身 reference 告警
  const skillMd = allFiles.find(({ path }) => path === join(SKILLS_DIR, name, 'SKILL.md'));
  if (!skillMd) return;
  const edgesFor = (content) => {
    const targets = new Set();
    // 裸文件名式(不带 references/ 前缀,如 `04-monorepo-nesting.md`)
    for (const f of refFiles) if (content.includes(f)) targets.add(f);
    FULL_REF.lastIndex = 0;
    let m;
    while ((m = FULL_REF.exec(content)) !== null) {
      if (refFiles.includes(m[1])) targets.add(m[1]);
    }
    const abbr = /references\/(\d{2})(?![\w.-])/g;
    while ((m = abbr.exec(content)) !== null) {
      for (const f of refFiles) if (f.startsWith(`${m[1]}-`)) targets.add(f);
    }
    return targets;
  };
  const visited = new Set();
  const queue = [...edgesFor(skillMd.content)];
  while (queue.length) {
    const f = queue.shift();
    if (visited.has(f)) continue;
    visited.add(f);
    const file = allFiles.find(({ path }) => path === join(refDir, f));
    if (file) queue.push(...edgesFor(file.content));
  }
  for (const f of refFiles) {
    if (!visited.has(f)) {
      warn(name, `references/${f} 从本技能 SKILL.md 沿指针走不到(仅其他文件可达或纯孤儿)`);
    }
  }
}

// ── ② plugin-map 映射完整性 ──────────────────────────────

function validatePluginMap() {
  if (!existsSync(PLUGIN_MAP)) { warn('plugin-map', '无 plugin-map.json,跳过'); return; }
  let map;
  try { map = JSON.parse(readFileSync(PLUGIN_MAP, 'utf8')); }
  catch (e) { err('plugin-map', `JSON 解析失败: ${e.message}`); return; }

  const seen = new Map(); // skillName -> groupName
  for (const [groupName, g] of Object.entries(map.groups || {})) {
    for (const skillName of g.skills || []) {
      if (!existsSync(join(SKILLS_DIR, skillName))) {
        err(`group:${groupName}`, `成员 "${skillName}" 在 skills/ 不存在`);
      }
      if (seen.has(skillName)) {
        err(`group:${groupName}`, `skill "${skillName}" 重复映射到 "${seen.get(skillName)}" 与 "${groupName}"`);
      } else {
        seen.set(skillName, groupName);
      }
    }
  }
}

// ── 主入口 ───────────────────────────────────────────────

function main() {
  const asJson = process.argv.includes('--json');

  const skillDirs = readdirSync(SKILLS_DIR)
    .filter(d => !d.startsWith('.') && statSync(join(SKILLS_DIR, d)).isDirectory());

  const allFiles = listContentFiles(SKILLS_DIR)
    .map(p => ({ path: p, content: readFileSync(p, 'utf8') }));
  const allRefFiles = collectAllRefFiles(skillDirs);
  for (const name of skillDirs) {
    validateFrontmatter(name);
    validateReferences(name, allFiles, allRefFiles);
    validateReachability(name, allFiles);
  }
  validatePluginMap();

  if (asJson) {
    console.log(JSON.stringify({ errors, warnings, ok: errors.length === 0 }, null, 2));
  } else {
    for (const w of warnings) console.log(`⚠ ${w}`);
    for (const e of errors) console.log(`✗ ${e}`);
    if (errors.length === 0) {
      console.log(`✓ 校验通过: ${skillDirs.length} 个技能 frontmatter + 引用 + 可达性 + 映射均合规`);
    } else {
      console.log(`\n共 ${errors.length} 个错误`);
    }
  }

  process.exit(errors.length === 0 ? 0 : 1);
}

main();
