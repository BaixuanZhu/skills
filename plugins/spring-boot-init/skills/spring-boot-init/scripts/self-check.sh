#!/usr/bin/env bash
# self-check.sh —— spring-boot-init 初始化自检
# 检查项: ①占位符 {{...}} 零残留 ②com.example 包路径残留 ③(--validate) mvn validate
# 用法:   bash <技能目录>/scripts/self-check.sh <项目目录> [--validate]
# 退出码: 0=全过 1=有失败项 2=用法/目录错误
set -uo pipefail

target="${1:?用法: self-check.sh <项目目录> [--validate]}"
opt="${2:-}"

[ -d "$target" ] || { echo "✗ 目录不存在: $target"; exit 2; }
cd "$target" || exit 2

fail=0

# ① 占位符零残留（排除 target/ 构建产物与 .git/）
if grep -rn --exclude-dir=target --exclude-dir=.git '{{' .; then
  echo "✗ 占位符 {{...}} 有残留（见上）"
  fail=1
else
  echo "✓ 占位符零残留"
fi

# ② 包目录 / package 行已挪离 com.example
if grep -rn --exclude-dir=target --exclude-dir=.git 'com\.example' .; then
  echo "✗ 仍有 com.example 残留（包目录未挪到 groupId 路径）"
  fail=1
else
  echo "✓ 包路径无 com.example 残留"
fi

# ③ 可选：Maven 结构合法
if [ "$opt" = "--validate" ]; then
  mvn_bin="$(command -v mvn.cmd || command -v mvn || true)"
  if [ -z "$mvn_bin" ]; then
    echo "⚠ 未找到 mvn，跳过 validate"
  elif "$mvn_bin" -q validate; then
    echo "✓ mvn validate 通过"
  else
    echo "✗ mvn validate 失败（错误输出为 GBK 时用 iconv -f gbk -t utf-8 转码读）"
    fail=1
  fi
fi

if [ "$fail" -eq 0 ]; then echo "自检通过"; else echo "自检未通过"; fi
exit "$fail"
