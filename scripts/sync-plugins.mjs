#!/usr/bin/env node
// sync-plugins.mjs —— 把 skills/ 的改动同步到 plugins/ + marketplace.json
//
// 真值源:
//   - skills/<name>/SKILL.md frontmatter 的 version  → 版本号唯一源头
//   - skills/<name>/ 全部文件                        → 内容唯一源头
//
// 不动(独立维护):
//   - marketplace.json 的 description/category/keywords/source
//   - plugin.json 的 description/author
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
  const marketplaceByName = new Map(marketplace.plugins.map(p => [p.name, p]));

  for (const name of skillDirs) {
    const skillDir = join(SKILLS_DIR, name);
    const fm = readSkillFrontmatter(skillDir);
    if (!fm?.version) {
      report.warnings.push(`${name}: SKILL.md 缺 version 字段,跳过`);
      continue;
    }

    const pluginDir = join(PLUGINS_DIR, name);
    const pluginJsonPath = join(pluginDir, '.claude-plugin', 'plugin.json');
    const skillDstDir = join(pluginDir, 'skills', name);

    // 边界:skills/ 有但 plugins/ 没有的技能(新增未初始化)→ 警告,不自动建
    if (!existsSync(pluginJsonPath)) {
      report.warnings.push(`${name}: plugins/${name}/ 不存在(新增技能?需手动建 .claude-plugin/plugin.json + skills/${name}/ 结构后才能同步)`);
      continue;
    }

    // ① 内容镜像:skills/<name>/ → plugins/<name>/skills/<name>/
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

    // ② plugin.json version 同步(只改 version,保留 name/description/author)
    const pj = JSON.parse(readFileSync(pluginJsonPath, 'utf8'));
    if (pj.version !== fm.version) {
      pj.version = fm.version;
      writeFileSync(pluginJsonPath, JSON.stringify(pj, null, 2) + '\n', 'utf8');
      report.versionsChanged.push(`${name} plugin.json: → ${fm.version}`);
    }

    // ③ marketplace.json version 同步(只改对应条目的 version)
    const entry = marketplaceByName.get(name);
    if (entry && entry.version !== fm.version) {
      entry.version = fm.version;
      report.versionsChanged.push(`${name} marketplace.json: → ${fm.version}`);
    } else if (!entry) {
      report.warnings.push(`${name}: marketplace.json 无对应条目(需手动添加 source/category/keywords)`);
    }
  }

  // 写回 marketplace.json(若 version 有变更)
  if (report.versionsChanged.length > 0) {
    writeFileSync(MARKETPLACE, JSON.stringify(marketplace, null, 2) + '\n', 'utf8');
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

// ── pre-commit hook 安装 ──────────────────────────────────

const HOOK_CONTENT = `#!/bin/sh
# 自动生成 by scripts/sync-plugins.mjs --install
# 把 skills/ 的改动同步到 plugins/ + marketplace.json,加进本次 commit
node scripts/sync-plugins.mjs || { echo "❌ sync-plugins 失败,commit 中止"; exit 1; }
git add plugins/ .claude-plugin/marketplace.json 2>/dev/null || true
`;

function installHook() {
  const hookPath = join(ROOT, '.git', 'hooks', 'pre-commit');
  const hooksDir = join(ROOT, '.git', 'hooks');
  if (!existsSync(hooksDir)) mkdirSync(hooksDir, { recursive: true });
  writeFileSync(hookPath, HOOK_CONTENT, 'utf8');
  try { chmodSync(hookPath, 0o755); } catch { /* Windows 无 chmod 概念,无害 */ }
  console.log(`✅ pre-commit hook 已安装: ${relative(ROOT, hookPath)}`);
  console.log('   以后 git commit 时自动同步 skills/ → plugins/ + marketplace.json');
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
