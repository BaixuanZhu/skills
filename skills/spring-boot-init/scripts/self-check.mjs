#!/usr/bin/env node
// self-check.mjs —— spring-boot-init 初始化自检（零依赖，跨平台）
// 检查项: ①占位符 {{...}} 零残留 ②com.example 包路径残留 ③(--validate) mvn validate
// 用法:   node <技能目录>/scripts/self-check.mjs <项目目录> [--validate]
// 退出码: 0=全过 1=有失败项 2=用法/目录错误

import { readdirSync, readFileSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { spawnSync } from 'node:child_process';

const target = process.argv[2];
const doValidate = process.argv.includes('--validate');

if (!target) {
  console.error('用法: node self-check.mjs <项目目录> [--validate]');
  process.exit(2);
}

// 遍历项目文件，跳过 .git / target 等非源码目录
function listFiles(dir, out = []) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    if (e.name.startsWith('.') || e.name === 'target') continue;
    const full = join(dir, e.name);
    if (e.isDirectory()) listFiles(full, out);
    else out.push(full);
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
for (const { re, bad, ok } of [
  { re: /\{\{/, bad: '✗ 占位符 {{...}} 有残留（见上）', ok: '✓ 占位符零残留' },
  { re: /com\.example/, bad: '✗ 仍有 com.example 残留（包目录未挪到 groupId 路径）', ok: '✓ 包路径无 com.example 残留' },
]) {
  const hits = [];
  for (const f of files) {
    let text;
    try { text = readFileSync(f, 'utf8'); } catch { continue; }
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

// ③ 可选：Maven 结构合法（Windows 下自动调 mvn.cmd）
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
