#!/bin/sh
# 七阶段注入矩阵 + 池耗尽边界：每个阶段一个独立项目目录，断言注入的是对应 brief 块。
# 用法：sh tests/agile/stage.sh（解释器叫 python3 的环境：PY=python3 sh …）
cd "$(dirname "$0")" || exit 1
PY="${PY:-python}"

# -W 输出 Windows 原生路径（Git Bash 特有，JSON payload 里的 cwd 需要它）；其它环境退回 pwd
w() ( cd "$1" && { pwd -W 2>/dev/null || pwd; } )

AG="$(w ../../plugins/agile/scripts)/agile.py"
ROOT="$(w stage)"
PASS=0; FAIL=0

say() { printf '%-34s %s\n' "$1" "$2"; }

expect() {  # expect <目录> <期望阶段> <期望包含的词>
  out=$($PY "$AG" brief "$ROOT/$1" 2>&1)
  stage=$(printf '%s' "$out" | head -1)
  if printf '%s' "$stage" | grep -q "$2" && printf '%s' "$out" | grep -q "$3"; then
    say "$1 → $2" "ok"; PASS=$((PASS+1))
  else
    say "$1 → $2" "FAIL"
    printf '%s\n' "$out" | sed 's/^/      /'
    FAIL=$((FAIL+1))
  fi
}

expect empty      "没有 agile-docs"     "新项目"
expect init       "阶段：init"          "战略层未起步"
expect arch       "阶段：architecture"  "阶段 B"
expect backlog    "阶段：backlog"       "待办池没有"
expect sprint     "阶段：sprint"        "容量三项"
expect active     "阶段：active"        "Sprint 进行中"
expect backfill   "阶段：backfill"      "未闭环回填"
expect conflict   "阶段：conflict"      "有冲突待裁决"

# 池耗尽边界：条目全部「已完成」时撑不起 Sprint（agile-sprint §0 取条前置），
# 应落回 backlog 段提示补池；但有进行中 Sprint 时进行中比建池靠前，仍判 active。
expect exhausted  "阶段：backlog"       "待办池没有"
expect active_dry "阶段：active"        "Sprint 进行中"

echo
echo "PASS=$PASS FAIL=$FAIL"
