#!/usr/bin/env node
// sync-plugins.mjs —— 把 skills/ 的改动同步到 plugins/ + 两份 marketplace.json
//
// 真值源:
//   - skills/<name>/SKILL.md frontmatter 的 version  → 版本号唯一源头
//   - skills/<name>/ 全部文件                        → 内容唯一源头
//
// 不动(独立维护):
//   - 两份 marketplace.json(.claude-plugin/ 与 .agents/plugins/) 的 description/category/keywords/source
//   - plugin.json(.claude-plugin 与 .codex-plugin) 的 description/author 等非 version 字段
//
// 用法:
//   node scripts/sync-plugins.mjs            # 同步,退出码 0(有改动也返回 0,hook 会 git add)
//   node scripts/sync-plugins.mjs --install  # 把 pre-commit hook 装到 .git/hooks/
//   node scripts/sync-plugins.mjs --check    # 只检查不写,有未同步差异则退出码 1(CI 用)

import { readFileSync, writeFileSync, existsSync, readdirSync, statSync, mkdirSync, rmSync, cpSync, chmodSync } from 'node:fs';
import { join, dirname, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import yaml from 'js-yaml';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const SKILLS_DIR = join(ROOT, 'skills');
const PLUGINS_DIR = join(ROOT, 'plugins');
const MARKETPLACE = join(ROOT, '.claude-plugin', 'marketplace.json');
const AGENTS_MARKETPLACE = join(ROOT, '.agents', 'plugins', 'marketplace.json');
const PLUGIN_MAP = join(__dirname, 'plugin-map.json');

// ── 加载 skill→plugin 分组映射 ────────────────────────────
// plugin-map.json 声明「多个 skill 归属 1 个 plugin」的映射。
// 反向索引: skillName → { group, versionStrategy }
// 不在映射里的 skill 走默认 1:1 逻辑（plugins/<name>/skills/<name>/）。
function loadPluginMap() {
  if (!existsSync(PLUGIN_MAP)) return { skillToGroup: new Map(), groups: {} };
  const raw = JSON.parse(readFileSync(PLUGIN_MAP, 'utf8'));
  const skillToGroup = new Map();
  const groups = raw.groups || {};
  for (const [groupName, g] of Object.entries(groups)) {
    for (const skillName of (g.skills || [])) {
      skillToGroup.set(skillName, { group: groupName, versionStrategy: g.version || 'max' });
    }
  }
  return { skillToGroup, groups };
}

const { skillToGroup, groups: PLUGIN_GROUPS } = loadPluginMap();

// 版本聚合:max 策略 = 取组内所有 skill 版本的最大值;
// 组内容有变化但聚合版本 ≤ 插件当前版本时(低版本成员更新,max 不动),bump patch 保证插件版本反映内容变化,
// 否则插件市场版本号不变、已装用户收不到更新提示。
function aggregateGroupVersion(groupName, skillVersions, currentPluginVersion, anyContentChanged) {
  const strategy = PLUGIN_GROUPS[groupName]?.version || 'max';
  let agg;
  if (strategy === 'max') {
    agg = skillVersions.sort((a, b) => compareVersions(b, a))[0];
  } else {
    throw new Error(`未知 version 策略: ${strategy} (group ${groupName})`);
  }
  if (currentPluginVersion && compareVersions(agg, currentPluginVersion) < 0) {
    agg = currentPluginVersion;  // 版本只升不降(成员 version 回退时不降插件版本)
  }
  if (anyContentChanged && currentPluginVersion && compareVersions(agg, currentPluginVersion) <= 0) {
    agg = bumpPatch(currentPluginVersion);
  }
  return agg;
}

// patch 位 +1(1.4.1 → 1.4.2)
function bumpPatch(version) {
  const p = String(version).split('.');
  p[2] = (Number(p[2]) || 0) + 1;
  return p.join('.');
}

// 语义化版本比较(a > b → 正数)
function compareVersions(a, b) {
  const pa = String(a).split('.').map(Number);
  const pb = String(b).split('.').map(Number);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const da = pa[i] || 0, db = pb[i] || 0;
    if (da !== db) return da - db;
  }
  return 0;
}

// ── 工具函数 ──────────────────────────────────────────────

function readSkillFrontmatter(skillDir) {
  const skillMd = join(skillDir, 'SKILL.md');
  if (!existsSync(skillMd)) return null;
  const text = readFileSync(skillMd, 'utf8');
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) throw new Error(`无法解析 frontmatter: ${relative(ROOT, skillMd)}/SKILL.md`);
  return yaml.load(m[1]);
}

function listSkillFiles(skillDir) {
  const out = [];
  const walk = (dir, base = '') => {
    for (const entry of readdirSync(dir)) {
      // 跳过隐藏目录/文件(如 .DS_Store)
      if (entry.startsWith('.')) continue;
      const full = join(dir, entry);
      const rel = base ? `${base}/${entry}` : entry;
      if (statSync(full).isDirectory()) walk(full, rel);
      else out.push(rel);
    }
  };
  walk(skillDir);
  return out;
}

function syncDir(src, dst) {
  // rsync 式:清空目标,全量复制(避免嵌套重复坑)
  if (existsSync(dst)) rmSync(dst, { recursive: true, force: true });
  mkdirSync(dst, { recursive: true });
  cpSync(src, dst, { recursive: true, dereference: true });
}

// ── 核心同步逻辑 ──────────────────────────────────────────

function sync() {
  const report = { filesChanged: [], versionsChanged: [], warnings: [] };

  const skillDirs = readdirSync(SKILLS_DIR)
    .filter(d => !d.startsWith('.') && statSync(join(SKILLS_DIR, d)).isDirectory());

  const marketplace = JSON.parse(readFileSync(MARKETPLACE, 'utf8'));
  const agentsMarketplace = existsSync(AGENTS_MARKETPLACE) ? JSON.parse(readFileSync(AGENTS_MARKETPLACE, 'utf8')) : null;
  const marketplaceByName = new Map(marketplace.plugins.map(p => [p.name, p]));
  const agentsByName = new Map((agentsMarketplace?.plugins || []).map(p => [p.name, p]));

  // 收集每个 group 的成员 skill 版本与内容变化标志(用于版本聚合)
  const groupSkillVersions = {};  // groupName → [{name, version, changed}]

  for (const name of skillDirs) {
    const skillDir = join(SKILLS_DIR, name);
    const fm = readSkillFrontmatter(skillDir);
    if (!fm?.version) {
      report.warnings.push(`${name}: SKILL.md 缺 version 字段,跳过`);
      continue;
    }

    // 判断 skill 归属:在 plugin-map.json 的 group 里 → plugin 名取 group 名;否则 1:1
    const mapping = skillToGroup.get(name);
    const pluginName = mapping ? mapping.group : name;

    const pluginDir = join(PLUGINS_DIR, pluginName);
    const pluginJsonPath = join(pluginDir, '.claude-plugin', 'plugin.json');
    const skillDstDir = join(pluginDir, 'skills', name);

    // 边界:skills/ 有但 plugins/ 没有的技能(新增未初始化)→ 警告,不自动建
    if (!existsSync(pluginJsonPath)) {
      report.warnings.push(`${name}: plugins/${pluginName}/ 不存在(新增技能?需手动建 .claude-plugin/plugin.json + skills/ 结构后才能同步)`);
      continue;
    }

    // ① 内容镜像:skills/<name>/ → plugins/<pluginName>/skills/<name>/
    const beforeFiles = existsSync(skillDstDir) ? listSkillFiles(skillDstDir).sort().join('\n') : '';
    const afterFiles = listSkillFiles(skillDir).sort().join('\n');
    const contentChanged = beforeFiles !== afterFiles ||
      !existsSync(skillDstDir) ||
      hasContentDiff(skillDir, skillDstDir);

    if (contentChanged) {
      syncDir(skillDir, skillDstDir);
      report.filesChanged.push(name);
    } else {
      // 即使文件列表相同,逐文件比对内容(上面的 hasContentDiff 已覆盖,此处冗余保险)
      // 无变化则不动
    }

    // 收集 group 成员版本(稍后统一聚合);非 group skill 收集自身版本供 1:1 同步
    if (mapping) {
      (groupSkillVersions[mapping.group] = groupSkillVersions[mapping.group] || []).push({ name, version: fm.version, changed: contentChanged });
    } else {
      // ② 1:1 插件:双 manifest(Claude + Codex)version 同步(只改 version,保留其余字段)
      syncManifestVersion(pluginJsonPath, fm.version, `${name} .claude-plugin/plugin.json`, report);
      syncManifestVersion(join(pluginDir, '.codex-plugin', 'plugin.json'), fm.version, `${name} .codex-plugin/plugin.json`, report);

      // ③ 1:1 两份 marketplace.json version 同步(只改对应条目的 version)
      setMarketplaceVersion(marketplaceByName, name, fm.version, `${name} .claude-plugin/marketplace.json`, report);
      setMarketplaceVersion(agentsByName, name, fm.version, `${name} .agents/plugins/marketplace.json`, report);
    }
  }

  // ②③ group 插件:版本聚合后统一同步 plugin.json + marketplace.json
  for (const [groupName, members] of Object.entries(groupSkillVersions)) {
    if (members.length === 0) continue;
    const pluginDir = join(PLUGINS_DIR, groupName);
    const pluginJsonPath = join(pluginDir, '.claude-plugin', 'plugin.json');
    const versions = members.map(m => m.version);
    const anyContentChanged = members.some(m => m.changed);
    // 当前插件版本:读 .claude-plugin/plugin.json(不存在时跳过 bump 判定,直接用聚合值)
    let currentPluginVersion = null;
    if (existsSync(pluginJsonPath)) {
      currentPluginVersion = JSON.parse(readFileSync(pluginJsonPath, 'utf8')).version || null;
    }
    const aggVersion = aggregateGroupVersion(groupName, versions, currentPluginVersion, anyContentChanged);

    // 双 manifest(Claude + Codex)version 同步(只改 version,保留其余字段)
    syncManifestVersion(pluginJsonPath, aggVersion, `${groupName} .claude-plugin/plugin.json`, report);
    syncManifestVersion(join(pluginDir, '.codex-plugin', 'plugin.json'), aggVersion, `${groupName} .codex-plugin/plugin.json`, report);

    setMarketplaceVersion(marketplaceByName, groupName, aggVersion, `${groupName} .claude-plugin/marketplace.json`, report);
    setMarketplaceVersion(agentsByName, groupName, aggVersion, `${groupName} .agents/plugins/marketplace.json`, report);
  }

  // 写回两份 marketplace.json(若 version 有变更)
  if (report.versionsChanged.length > 0) {
    writeFileSync(MARKETPLACE, JSON.stringify(marketplace, null, 2) + '\n', 'utf8');
    if (agentsMarketplace) writeFileSync(AGENTS_MARKETPLACE, JSON.stringify(agentsMarketplace, null, 2) + '\n', 'utf8');
  }

  return report;
}

// 逐文件比对内容(检测内容改动而不仅是文件名变化)
function hasContentDiff(srcDir, dstDir) {
  const srcFiles = listSkillFiles(srcDir);
  const dstFiles = existsSync(dstDir) ? listSkillFiles(dstDir) : [];
  if (srcFiles.length !== dstFiles.length) return true;
  for (const f of srcFiles) {
    if (!dstFiles.includes(f)) return true;
    const a = readFileSync(join(srcDir, f), 'utf8');
    const b = readFileSync(join(dstDir, f), 'utf8');
    if (a !== b) return true;
  }
  return false;
}

// 同步单个 manifest(plugin.json)的 version——只改 version,保留其余字段。
// 供 .claude-plugin/plugin.json 与 .codex-plugin/plugin.json 共用;缺失时仅告警不中断。
function syncManifestVersion(jsonPath, newVersion, label, report) {
  if (!existsSync(jsonPath)) {
    report.warnings.push(`${label}: ${relative(ROOT, jsonPath)} 不存在,version 不同步`);
    return;
  }
  const data = JSON.parse(readFileSync(jsonPath, 'utf8'));
  if (data.version !== newVersion) {
    data.version = newVersion;
    writeFileSync(jsonPath, JSON.stringify(data, null, 2) + '\n', 'utf8');
    report.versionsChanged.push(`${label}: → ${newVersion}`);
  }
}

// 同步单份 marketplace.json 里某条目的 version——只改 version,保留其余字段。
// 供 .claude-plugin/ 与 .agents/plugins/ 两份 marketplace 共用;条目缺失仅告警不中断。
function setMarketplaceVersion(byName, name, version, label, report) {
  const entry = byName.get(name);
  if (entry) {
    if (entry.version !== version) {
      entry.version = version;
      report.versionsChanged.push(`${label}: → ${version}`);
    }
  } else {
    report.warnings.push(`${label}: 无对应条目(需手动添加)`);
  }
}

// ── pre-commit hook 安装 ──────────────────────────────────

const HOOK_CONTENT = `#!/bin/sh
# 自动生成 by scripts/sync-plugins.mjs --install
# 把 skills/ 的改动同步到 plugins/(双 manifest) + 两份 marketplace.json,加进本次 commit
node scripts/sync-plugins.mjs || { echo "❌ sync-plugins 失败,commit 中止"; exit 1; }
git add plugins/ .claude-plugin/marketplace.json .agents/plugins/marketplace.json 2>/dev/null || true
`;

function installHook() {
  const hookPath = join(ROOT, '.git', 'hooks', 'pre-commit');
  const hooksDir = join(ROOT, '.git', 'hooks');
  if (!existsSync(hooksDir)) mkdirSync(hooksDir, { recursive: true });
  writeFileSync(hookPath, HOOK_CONTENT, 'utf8');
  try { chmodSync(hookPath, 0o755); } catch { /* Windows 无 chmod 概念,无害 */ }
  console.log(`✅ pre-commit hook 已安装: ${relative(ROOT, hookPath)}`);
  console.log('   以后 git commit 时自动同步 skills/ → plugins/(双 manifest) + 两份 marketplace.json');
}

// ─-- 主入口 ─────────────────────────────────────────────

function main() {
  const args = process.argv.slice(2);

  if (args.includes('--install')) {
    installHook();
    return;
  }

  const checkOnly = args.includes('--check');
  const report = sync();

  // 输出报告
  if (report.filesChanged.length) {
    console.log('内容同步:');
    for (const n of report.filesChanged) console.log(`  ✓ ${n}`);
  }
  if (report.versionsChanged.length) {
    console.log('版本号更新:');
    for (const v of report.versionsChanged) console.log(`  ✓ ${v}`);
  }
  if (report.warnings.length) {
    console.log('警告:');
    for (const w of report.warnings) console.log(`  ⚠ ${w}`);
  }
  const total = report.filesChanged.length + report.versionsChanged.length;
  if (total === 0 && report.warnings.length === 0) {
    console.log('✓ skills/ 与 plugins/ 已同步,无需改动');
  }

  // --check 模式:有改动则失败(CI 兑底用)
  if (checkOnly && total > 0) {
    console.error('\n❌ 检测到未同步的改动(本地未跑 sync 或未装 hook)');
    process.exit(1);
  }
}

main();
