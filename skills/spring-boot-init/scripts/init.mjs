#!/usr/bin/env node
// init.mjs —— spring-boot-init 脚手架生成器（零依赖，跨平台）
// 从内置 Maven 父子模板生成项目：复制 → 替换占位符 → 挪包目录 → 模块塑形（重命名 / 单模块裁剪）→ 残留终检
// 用法:
//   node init.mjs <目标目录> --group <groupId> --artifact <artifactId>
//                 [--version 1.0.0-SNAPSHOT] [--jdk 21] [--boot 3.5.16]
//                 [--core <库模块名>] [--app <可执行模块名>] [--single]
// --single   单模块形态：删掉库模块（sample-core）目录及其全部引用
// 退出码: 0=成功 1=生成物有残留 2=用法错误

import { readdirSync, readFileSync, writeFileSync, mkdirSync, rmSync, cpSync, renameSync, existsSync, statSync } from 'node:fs';
import { join, dirname, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const TEMPLATE = join(dirname(fileURLToPath(import.meta.url)), '..', 'assets', 'maven-multimodule');

// ── 参数解析（严格模式：未知参数 / 缺值 / 多余位置参数直接拒绝，杜绝 --single=true 被静默吞掉）──
const args = process.argv.slice(2);
const target = args[0];
const opt = { single: false };
const KNOWN = new Set(['group', 'artifact', 'version', 'jdk', 'boot', 'core', 'app', 'single']);
for (let i = 1; i < args.length; i++) {
  const a = args[i];
  if (!a.startsWith('--')) {
    console.error(`✗ 多余的位置参数: ${a}（只接受一个目标目录 + 选项）`);
    process.exit(2);
  }
  const eq = a.indexOf('=');
  const key = eq === -1 ? a.slice(2) : a.slice(2, eq);
  if (!KNOWN.has(key)) {
    console.error(`✗ 未知参数 --${key}（支持: group / artifact / version / jdk / boot / core / app / single）`);
    process.exit(2);
  }
  if (key === 'single') {
    if (eq !== -1 && a.slice(eq + 1) !== 'true') {
      console.error('✗ --single 不接受值（要启用就写 --single）');
      process.exit(2);
    }
    opt.single = true;
    continue;
  }
  const v = eq === -1 ? args[++i] : a.slice(eq + 1);
  if (v === undefined || v.startsWith('--')) {
    console.error(`✗ --${key} 缺值`);
    process.exit(2);
  }
  opt[key] = v;
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

// groupId 直接用作 Java 包路径、artifact/模块名用作目录名——非法输入直接拒绝，不生成坏结构
if (!/^[A-Za-z_$][A-Za-z0-9_$]*(\.[A-Za-z_$][A-Za-z0-9_$]*)*$/.test(group)) {
  console.error(`✗ --group ${group} 不是合法 Java 包名（每段以字母/_/$ 开头，仅含字母/数字/_/$，以 . 分隔）`);
  process.exit(2);
}
const KEYWORDS = new Set(['abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char', 'class', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum', 'extends', 'final', 'finally', 'float', 'for', 'goto', 'if', 'implements', 'import', 'instanceof', 'int', 'interface', 'long', 'native', 'new', 'package', 'private', 'protected', 'public', 'return', 'short', 'static', 'strictfp', 'super', 'switch', 'synchronized', 'this', 'throw', 'throws', 'transient', 'try', 'void', 'volatile', 'while', '_', 'true', 'false', 'null']);
const kwSeg = group.split('.').find((s) => KEYWORDS.has(s));
if (kwSeg) {
  console.error(`✗ --group ${group} 的包段 "${kwSeg}" 是 Java 保留字，不能用作包名`);
  process.exit(2);
}
if (group.split('.').some((s) => s.length > 64) || group.length > 200) {
  console.error('✗ --group 过长（每段 ≤64 字符、总长 ≤200），生成路径会超出文件系统限制');
  process.exit(2);
}
for (const n of [artifact, opt.core, opt.app].filter(Boolean)) {
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(n)) {
    console.error(`✗ 名称 ${n} 含路径不安全字符（只允许字母、数字、点、下划线、连字符，且以字母或数字开头）`);
    process.exit(2);
  }
  if (n.endsWith('.')) {
    console.error(`✗ 名称 ${n} 不能以点结尾（Win32 下该目录不可寻址，Maven 找不到子模块）`);
    process.exit(2);
  }
}
if (opt.single && opt.core) {
  console.error('✗ --single 与 --core 互斥：单模块形态没有库模块，请二选一');
  process.exit(2);
}
for (const [flag, name] of [['--core', coreName], ['--app', appName]]) {
  const ln = name.toLowerCase();
  if (ln === 'sample-core' || ln === 'sample-app') {
    console.error(`✗ ${flag} 生效名 ${name} 与模板目录名冲突（sample-core / sample-app 为内部保留名，含大小写变体）`);
    process.exit(2);
  }
  if (ln === 'pom.xml') {
    console.error(`✗ ${flag} 生效名 ${name} 会顶替根 pom.xml 文件，模块目录禁止叫这个名字`);
    process.exit(2);
  }
  if (ln === 'target') {
    console.error(`✗ ${flag} 生效名 ${name} 撞 Maven 构建输出目录 target/——mvn clean 会把整个模块删掉`);
    process.exit(2);
  }
  if (name === artifact && (flag === '--app' || !opt.single)) {
    console.error(`✗ ${flag} 生效名 ${name} 与根 artifactId 同名——Maven reactor 里 GAV 重复，validate 必失败`);
    process.exit(2);
  }
}
if (!opt.single && coreName === appName) {
  console.error(`✗ --core 与 --app 不能同名（${coreName}）：目录与模块名会互相覆盖`);
  process.exit(2);
}
if (!opt.single && coreName.toLowerCase() === appName.toLowerCase()) {
  console.error(`✗ --core 与 --app 不能仅大小写不同（${coreName} / ${appName}）：Windows 目录不区分大小写会互相覆盖`);
  process.exit(2);
}
if (!/^\d+\.\d+(\.\d+)?(-[A-Za-z0-9.-]+)?$/.test(boot)) {
  console.error(`✗ --boot ${boot} 不是合法版本号（形如 3.5.16）`);
  process.exit(2);
}
if (!/^\d+$/.test(jdk)) {
  console.error(`✗ --jdk ${jdk} 不是合法 JDK 版本号（形如 21）`);
  process.exit(2);
}
if (!/^\d+(\.\d+){0,2}(-[A-Za-z0-9.-]+)?$/.test(version)) {
  console.error(`✗ --version ${version} 不是合法版本号（形如 1.0.0-SNAPSHOT）`);
  process.exit(2);
}

// ── ① 复制模板（只做全新初始化，已有工程直接拒绝）────────
if (existsSync(target) && !statSync(target).isDirectory()) {
  console.error(`✗ 目标路径已存在且不是目录: ${target}`);
  process.exit(2);
}
if (existsSync(join(target, 'pom.xml'))) {
  console.error(`✗ ${target} 已有 pom.xml——本脚本只做全新初始化；已有工程加模块参照工程内现有结构即可`);
  process.exit(2);
}
const visibleEntries = existsSync(target) ? readdirSync(target).filter((n) => !n.startsWith('.')) : [];
if (visibleEntries.length) {
  console.error(`✗ ${target} 非空（含 ${visibleEntries.length} 个非隐藏条目）——本脚本只对空目录做全新初始化（隐藏条目如 .git 不影响）`);
  process.exit(2);
}
mkdirSync(target, { recursive: true });
cpSync(TEMPLATE, target, { recursive: true });
renameSync(join(target, 'gitignore.txt'), join(target, '.gitignore')); // 模板内非点名存放（发布平台只收白名单扩展名），落地即改回 .gitignore

const rootPom = join(target, 'pom.xml');
const corePom = join(target, 'sample-core', 'pom.xml');
const appPom = join(target, 'sample-app', 'pom.xml');
const yml = join(target, 'sample-app', 'src', 'main', 'resources', 'application.yml');
let root = readFileSync(rootPom, 'utf8').replace(/\r\n/g, '\n');
let core = readFileSync(corePom, 'utf8').replace(/\r\n/g, '\n');
let app = readFileSync(appPom, 'utf8').replace(/\r\n/g, '\n');
let y = readFileSync(yml, 'utf8').replace(/\r\n/g, '\n');

// ── ② 单模块裁剪：删 sample-core 的三处引用（模块行 / dependencyManagement 条目 / app 依赖；目录在④删除）──
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

// ── ③ 模块重命名（sample-core/sample-app 字符串与目录一次对齐；函数替换不回扫——名字含 sample-app/core 子串也不会被二次改写。
//    必须在 ④ 占位符展开之前：用户值（如 artifact 含 sample-app）写入后不再经过任何替换 pass，杜绝坐标腐蚀）──
const shape = (t) => t.replace(/sample-(core|app)/g, (_, m) => (m === 'core' ? coreName : appName));
root = shape(root);
core = shape(core);
app = shape(app);

// ── ④ 替换占位符（最后一步文本改写，之后不再回扫）─────────
const PH = {
  '{{GROUP_ID}}': group,
  '{{ARTIFACT_ID}}': artifact,
  '{{VERSION}}': version,
  '{{JAVA_VERSION}}': jdk,
  '{{BOOT_VERSION}}': boot,
};
const ph = (t) => { for (const [k, v] of Object.entries(PH)) t = t.split(k).join(v); return t; };
root = ph(root); core = ph(core); app = ph(app); y = ph(y);

writeFileSync(rootPom, root);
writeFileSync(appPom, app);
writeFileSync(yml, y);
if (opt.single) rmSync(join(target, 'sample-core'), { recursive: true, force: true });
else {
  writeFileSync(corePom, core);
  renameSync(join(target, 'sample-core'), join(target, coreName));
}
renameSync(join(target, 'sample-app'), join(target, appName));

// ── ⑤ 挪包目录：com/example → groupId 路径，改 package 行 ──
// 主类先暂存到 java 根、再清掉整个模板包壳 com/：目标包嵌在 com/example 之内（如 com.example.demo）也不会被连带删除
const javaDir = join(target, appName, 'src', 'main', 'java');
const toDir = join(javaDir, ...group.split('.'));
const staging = join(javaDir, 'Application.java.moving');
renameSync(join(javaDir, 'com', 'example', 'Application.java'), staging);
rmSync(join(javaDir, 'com'), { recursive: true, force: true });
mkdirSync(toDir, { recursive: true });
renameSync(staging, join(toDir, 'Application.java'));
const mainJava = join(toDir, 'Application.java');
writeFileSync(mainJava, readFileSync(mainJava, 'utf8').replace('package com.example;', `package ${group};`));

// ── ⑥ 残留终检（占位符 / com.example / 主类存在 / 顶层目录恰为模块集）──
function walk(dir, out = []) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    if (e.isDirectory() && e.name.startsWith('.')) continue; // 跳过 .git 等（目标目录允许只含 .git）
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
  // 仅当 groupId 自身包含 com.example（如 com.example.demo / com.example0.dev / org.foo.com.example）才先剥离再匹配——
  // 剥离只移除 groupId 的精确出现，不会遮蔽真残留；不含 com.example 的短 groupId（如 com）不剥离、不遮蔽
  const t2 = /com\.example/.test(group) ? t.split(group).join('') : t;
  if (t2.includes('{{')) { console.log(`✗ 残留占位符: ${rel}`); bad = 1; }
  if (/com\.example/.test(t2)) { console.log(`✗ 残留 com.example: ${rel}`); bad = 1; }
}
if (!existsSync(mainJava)) { console.log('✗ 主类缺失: app 模块 src/main/java 下无 Application.java'); bad = 1; }
const expectedDirs = (opt.single ? [appName] : [coreName, appName]).slice().sort();
const actualDirs = readdirSync(target, { withFileTypes: true })
  .filter((e) => e.isDirectory() && !e.name.startsWith('.'))
  .map((e) => e.name)
  .sort();
if (JSON.stringify(actualDirs) !== JSON.stringify(expectedDirs)) {
  console.log(`✗ 顶层目录与预期模块不符: 实际 [${actualDirs}]，预期 [${expectedDirs}]`);
  bad = 1;
}

console.log(`✓ 已生成 ${opt.single ? '单模块' : '多模块'}工程: ${target}`);
console.log(`  坐标 ${group}:${artifact}:${version}（Boot ${boot} / JDK ${jdk}）`);
console.log(`  模块: ${opt.single ? appName : `${coreName} + ${appName}`}`);
if (bad === 1) { console.log('✗ 生成物有残留，请检查'); process.exit(1); }
console.log('✓ 占位符与包路径零残留');
console.log('下一步: node <技能目录>/scripts/self-check.mjs <目标目录> --validate');
process.exit(0);
