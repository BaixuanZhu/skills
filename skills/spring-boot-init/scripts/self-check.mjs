#!/usr/bin/env node
// self-check.mjs —— spring-boot-init 初始化自检（零依赖，跨平台）
// 检查项: ①占位符 {{...}} 零残留 ②com.example 包路径残留 ③模块目录与根 <modules> 一一对应 ④可执行模块存在且含主类 ⑤package 声明与目录一致 ⑥(--validate) mvn validate
// 用法:   node <技能目录>/scripts/self-check.mjs <项目目录> [--validate]
// 退出码: 0=全过 1=有失败项 2=用法/目录错误

import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { spawnSync } from 'node:child_process';

const target = process.argv[2];
const doValidate = process.argv.includes('--validate');

if (!target) {
  console.error('用法: node self-check.mjs <项目目录> [--validate]');
  process.exit(2);
}

// 遍历项目文件：只跳过已知的非源码目录（.git / .idea / .vscode 与 src 树外的构建产物 target）；
// 其余点目录与点文件（.gitignore 等）都要扫——占位符 / com.example 残留可能藏在任意自建点目录里。
// target 只在 src 树外跳过——包路径里名为 target 的段（如 groupId com.target.x）是合法源码，不能误跳
function listFiles(dir, out = [], inSrc = false) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, e.name);
    if (e.isDirectory()) {
      if (['.git', '.idea', '.vscode'].includes(e.name)) continue;
      if (e.name === 'target' && !inSrc) continue;
      listFiles(full, out, inSrc || e.name === 'src');
    } else out.push(full);
  }
  return out;
}

let files;
try {
  files = listFiles(target);
} catch {
  console.error(`✗ 目录不存在或不可读: ${target}`);
  process.exit(2);
}
const rel = (f) => relative(target, f).split(sep).join('/');

let fail = 0;

// ①② 前两查：逐文件逐行找残留（输出 文件:行号:内容 供定位）
// com.example 检查前先剥离根 pom 声明的 groupId（com.example0.dev 之类前缀不误伤）
const rootPomPath = files.find((f) => relative(target, f) === 'pom.xml') || null;
const rootGroup = (() => {
  if (!rootPomPath) return '';
  const m = readFileSync(rootPomPath, 'utf8').match(/<groupId>([^<]+)<\/groupId>/);
  return m ? m[1] : '';
})();

// Java 源码降噪：先解码 \uXXXX（javac 预处理语义）再剥块注释 / 行注释 / 文本块 / 字符串字面量，
// 末尾把未闭合块注释到 EOF 一并视作注释——注释、字符串、文本块、unicode 转义、畸形未闭合注释里的
// 伪造内容（假 main 签名 / 假 package 行）都骗不过
const stripNoise = (t) => t
  .replace(/\\u([0-9a-fA-F]{4})/g, (_, h) => String.fromCharCode(parseInt(h, 16)))
  .replace(/\/\*[\s\S]*?\*\//g, '')
  .replace(/\/\/[^\n]*/g, '')
  .replace(/"""[\s\S]*?"""/g, '""""""')
  .replace(/"(?:[^"\\\n]|\\.)*"/g, '""')
  .replace(/\/\*[\s\S]*$/, '');

for (const { re, bad, ok } of [
  { re: /\{\{/, bad: '✗ 占位符 {{...}} 有残留（见上）', ok: '✓ 占位符零残留' },
  { re: /com\.example/, bad: '✗ 仍有 com.example 残留（包目录未挪到 groupId 路径）', ok: '✓ 包路径无 com.example 残留' },
]) {
  const hits = [];
  for (const f of files) {
    let text;
    try { text = readFileSync(f, 'utf8'); } catch { continue; }
    // 仅当 groupId 自身包含 com.example 才先剥离（剥离只移除 groupId 精确出现；不含则不剥离，防短 groupId 如 com 遮蔽真残留）
    if (rootGroup && /com\.example/.test(rootGroup)) text = text.split(rootGroup).join('');
    text.split(/\r?\n/).forEach((line, i) => {
      if (re.test(line)) hits.push(`${rel(f)}:${i + 1}:${line.trim()}`);
    });
  }
  if (hits.length) {
    for (const h of hits) console.log(h);
    console.log(bad);
    fail = 1;
  } else {
    console.log(ok);
  }
}

// ③ 模块目录与根 <modules> 一一对应（防孤儿目录 / 声明了但目录缺失；只查一级子目录——本技能产物为扁平父子结构）
if (!rootPomPath) {
  console.log('✗ 缺根 pom.xml——自检对象不是 Maven 工程');
  fail = 1;
}
const pomDirs = rootPomPath
  ? readdirSync(target, { withFileTypes: true })
      .filter((e) => e.isDirectory() && !e.name.startsWith('.') && e.name !== 'target')
      .map((e) => e.name)
      .filter((d) => existsSync(join(target, d, 'pom.xml')))
  : [];
if (rootPomPath) {
  const rootPomText = readFileSync(rootPomPath, 'utf8').replace(/<!--[\s\S]*?-->/g, '');
  const modules = [...rootPomText.matchAll(/<module>([^<]+)<\/module>/g)].map((m) => m[1].trim());
  const orphan = pomDirs.filter((d) => !modules.includes(d));
  const missing = modules.filter((m) => !pomDirs.includes(m));
  for (const d of orphan) console.log(`✗ 孤儿模块目录（含 pom.xml 但不在根 <modules>）: ${d}`);
  for (const m of missing) console.log(`✗ 根 <modules> 声明了但目录缺失: ${m}`);
  if (orphan.length || missing.length) fail = 1;
  else console.log('✓ 模块目录与根 <modules> 一一对应');
}

// ④ 可执行模块必须存在且含主类（pom 声明 spring-boot-maven-plugin 的模块，src/main/java 下须有真实 main 方法——
//    先剥离注释与字符串字面量再按签名匹配，注释/字符串里的 "static void main" 骗不过）
if (rootPomPath) {
  // 激活判定：剥 XML 注释、整段剔除 pluginManagement（管理≠激活）/ profiles（未激活）/ properties（属性值伪造）/
  // reporting（报告节非构建插件）后，须出现真实的 <plugin>…<artifactId> 声明序列——散落字符串骗不过
  const isActive = (pomText) => /<plugin>\s*(?:<groupId>[^<]*<\/groupId>\s*)?<artifactId>spring-boot-maven-plugin<\/artifactId>/.test(
    pomText
      .replace(/<!--[\s\S]*?-->/g, '')
      .replace(/<pluginManagement>[\s\S]*?<\/pluginManagement>/g, '')
      .replace(/<profiles>[\s\S]*?<\/profiles>/g, '')
      .replace(/<properties>[\s\S]*?<\/properties>/g, '')
      .replace(/<reporting>[\s\S]*?<\/reporting>/g, ''),
  );
  const execDirs = pomDirs.filter((d) => isActive(readFileSync(join(target, d, 'pom.xml'), 'utf8')));
  if (!execDirs.length) {
    console.log('✗ 无可执行模块——app 模块须在 <build><plugins> 声明 spring-boot-maven-plugin（repackage）');
    fail = 1;
  } else {
    let mainMissing = false;
    for (const d of execDirs) {
      const javaRoot = join(target, d, 'src', 'main', 'java') + sep;
      const hasMain = files.some(
        (f) => f.startsWith(javaRoot) && f.endsWith('.java')
          && /\bstatic\s+void\s+main\s*\(\s*(?:final\s+)?(?:[A-Za-z_$][\w$]*\.)*String\s*(?:\[\s*\]|\.\.\.)/.test(stripNoise(readFileSync(f, 'utf8'))),
      );
      if (!hasMain) { console.log(`✗ 可执行模块缺主类（src/main/java 无 static void main(String...) 方法）: ${d}`); mainMissing = true; }
    }
    if (mainMissing) fail = 1;
    else console.log('✓ 可执行模块均含主类');
  }
}

// ⑤ package 声明与目录路径一致（.java 的 package 行必须等于它在 src/main/java|src/test/java 下的目录）
let pkgMismatch = false;
for (const f of files) {
  if (!f.endsWith('.java')) continue;
  const r = rel(f);
  const anchor = r.match(/^(.*\/src\/(?:main|test)\/java)\/(.+)$/);
  if (!anchor) continue;
  const dirParts = anchor[2].split('/');
  dirParts.pop();
  const expected = dirParts.join('.');
  const decl = (stripNoise(readFileSync(f, 'utf8')).match(/^\s*package\s+([\w.$]+)\s*;/m) || [])[1] || '';
  if (decl !== expected) {
    console.log(`✗ package 声明与目录不一致: ${r}（声明 ${decl || '（无）'}，目录 ${expected || '（默认包）'}）`);
    pkgMismatch = true;
  }
}
if (pkgMismatch) fail = 1;
else console.log('✓ package 声明与目录路径一致');

// ⑥ 可选：Maven 结构合法（Windows 下自动调 mvn.cmd）
if (doValidate) {
  const isWin = process.platform === 'win32';
  const bin = isWin ? 'mvn.cmd' : 'mvn';
  const probe = spawnSync(isWin ? 'where' : 'which', [bin], { shell: isWin });
  if (probe.status !== 0) {
    console.log('⚠ 未找到 mvn，跳过 validate');
  } else {
    const r = spawnSync(bin, ['-q', 'validate'], { cwd: target, stdio: 'inherit', shell: isWin });
    if (r.status === 0) console.log('✓ mvn validate 通过');
    else {
      console.log('✗ mvn validate 失败（错误输出为 GBK 时用 iconv -f gbk -t utf-8 转码读）');
      fail = 1;
    }
  }
}

console.log(fail === 0 ? '自检通过' : '自检未通过');
process.exit(fail);
