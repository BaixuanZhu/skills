#!/usr/bin/env node
// init.mjs —— spring-boot-init 脚手架生成器（零依赖，跨平台）
// 从内置 Maven 父子模板生成项目：复制 → 替换占位符 → 挪包目录 → 模块塑形（重命名 / 单模块裁剪）→ 残留终检
// 用法:
//   node init.mjs <目标目录> --group <groupId> --artifact <artifactId>
//                 [--version 1.0.0-SNAPSHOT] [--jdk 21] [--boot 3.5.16]
//                 [--core <库模块名>] [--app <可执行模块名>] [--single]
// --single   单模块形态：裁掉库模块（sample-core）及其全部引用
// 退出码: 0=成功 1=生成物有残留 2=用法错误

import { readdirSync, readFileSync, writeFileSync, mkdirSync, rmSync, cpSync, renameSync, existsSync } from 'node:fs';
import { join, dirname, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const TEMPLATE = join(dirname(fileURLToPath(import.meta.url)), '..', 'assets', 'maven-multimodule');

// ── 参数解析 ──────────────────────────────────────────────
const args = process.argv.slice(2);
const target = args[0];
const opt = { single: false };
for (let i = 1; i < args.length; i++) {
  const a = args[i];
  if (a === '--single') { opt.single = true; continue; }
  if (a.startsWith('--')) opt[a.slice(2)] = args[++i];
}

if (!target || !opt.group || !opt.artifact) {
  console.error('用法: node init.mjs <目标目录> --group <groupId> --artifact <artifactId> [--version V] [--jdk 21] [--boot 3.5.16] [--core 名] [--app 名] [--single]');
  process.exit(2);
}

const { group, artifact } = opt;
const version = opt.version || '1.0.0-SNAPSHOT';
const jdk = opt.jdk || '21';
const boot = opt.boot || '3.5.16';
const coreName = opt.core || `${artifact}-core`;
const appName = opt.app || `${artifact}-app`;

// ── ① 复制模板（只做全新初始化，已有工程直接拒绝）────────
if (existsSync(join(target, 'pom.xml'))) {
  console.error(`✗ ${target} 已有 pom.xml——本脚本只做全新初始化；已有工程加模块参照工程内现有结构即可`);
  process.exit(2);
}
mkdirSync(target, { recursive: true });
cpSync(TEMPLATE, target, { recursive: true });

const rootPom = join(target, 'pom.xml');
const corePom = join(target, 'sample-core', 'pom.xml');
const appPom = join(target, 'sample-app', 'pom.xml');
const yml = join(target, 'sample-app', 'src', 'main', 'resources', 'application.yml');
let root = readFileSync(rootPom, 'utf8').replace(/\r\n/g, '\n');
let core = readFileSync(corePom, 'utf8').replace(/\r\n/g, '\n');
let app = readFileSync(appPom, 'utf8').replace(/\r\n/g, '\n');
let y = readFileSync(yml, 'utf8').replace(/\r\n/g, '\n');

// ── ② 单模块裁剪：删 sample-core 的三处引用（模块行 / dependencyManagement 条目 / app 依赖）──
if (opt.single) {
  root = root
    .replace('        <module>sample-core</module>\n', '')
    .replace(
      '            <dependency>\n' +
      '                <groupId>{{GROUP_ID}}</groupId>\n' +
      '                <artifactId>sample-core</artifactId>\n' +
      '                <version>${revision}</version>\n' +
      '            </dependency>\n', '');
  app = app.replace(
    '        <dependency>\n' +
    '            <groupId>{{GROUP_ID}}</groupId>\n' +
    '            <artifactId>sample-core</artifactId>\n' +
    '        </dependency>\n', '');
}

// ── ③ 替换占位符 ──────────────────────────────────────────
const PH = {
  '{{GROUP_ID}}': group,
  '{{ARTIFACT_ID}}': artifact,
  '{{VERSION}}': version,
  '{{JAVA_VERSION}}': jdk,
  '{{BOOT_VERSION}}': boot,
};
const ph = (t) => { for (const [k, v] of Object.entries(PH)) t = t.split(k).join(v); return t; };
root = ph(root); core = ph(core); app = ph(app); y = ph(y);

// ── ④ 模块重命名（sample-core/sample-app 字符串与目录一次对齐）──
if (!opt.single) {
  root = root.split('sample-core').join(coreName);
  core = core.split('sample-core').join(coreName);
  app = app.split('sample-core').join(coreName);
}
root = root.split('sample-app').join(appName);
app = app.split('sample-app').join(appName);

writeFileSync(rootPom, root);
writeFileSync(corePom, core);
writeFileSync(appPom, app);
writeFileSync(yml, y);
if (!opt.single) renameSync(join(target, 'sample-core'), join(target, coreName));
renameSync(join(target, 'sample-app'), join(target, appName));

// ── ⑤ 挪包目录：com/example → groupId 路径，改 package 行 ──
const javaDir = join(target, appName, 'src', 'main', 'java');
const toDir = join(javaDir, ...group.split('.'));
mkdirSync(toDir, { recursive: true });
renameSync(join(javaDir, 'com', 'example', 'Application.java'), join(toDir, 'Application.java'));
const mainJava = join(toDir, 'Application.java');
writeFileSync(mainJava, readFileSync(mainJava, 'utf8').replace('package com.example;', `package ${group};`));
rmSync(join(javaDir, 'com', 'example'), { recursive: true, force: true });
if (group.split('.')[0] !== 'com') rmSync(join(javaDir, 'com'), { recursive: true, force: true });

// ── ⑥ 残留终检 ────────────────────────────────────────────
function walk(dir, out = []) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, e.name);
    if (e.isDirectory()) walk(full, out);
    else out.push(full);
  }
  return out;
}
let bad = 0;
for (const f of walk(target)) {
  let t;
  try { t = readFileSync(f, 'utf8'); } catch { continue; }
  const rel = relative(target, f);
  // 先剥离用户声明的 groupId（com.example0.dev 之类前缀不误伤），再查模板残留
  const t2 = t.split(group).join('');
  if (t2.includes('{{')) { console.log(`✗ 残留占位符: ${rel}`); bad = 1; }
  if (/com\.example/.test(t2)) { console.log(`✗ 残留 com.example: ${rel}`); bad = 1; }
}

console.log(`✓ 已生成 ${opt.single ? '单模块' : '多模块'}工程: ${target}`);
console.log(`  坐标 ${group}:${artifact}:${version}（Boot ${boot} / JDK ${jdk}）`);
console.log(`  模块: ${opt.single ? appName : `${coreName} + ${appName}`}`);
if (bad === 1) { console.log('✗ 生成物有残留，请检查'); process.exit(1); }
console.log('✓ 占位符与包路径零残留');
console.log('下一步: node <技能目录>/scripts/self-check.mjs <目标目录> --validate');
process.exit(0);
