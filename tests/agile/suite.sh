#!/usr/bin/env bash
# hook-prompt 回归矩阵：每个用例断言「有输出 / 无输出」+ 关键子串
# 用法：bash tests/agile/suite.sh（解释器叫 python3 的环境：PY=python3 …）
set -u
cd "$(dirname "$0")"
PLUGIN="$(cd ../../plugins/agile && pwd)"
PY="${PY:-python}"
AG="$PLUGIN/scripts/agile.py"
PASS=0; FAIL=0

# -W 输出 Windows 原生路径（Git Bash 特有，JSON payload 里的 cwd 需要它）；其它环境退回 pwd
w() ( cd "$1" && { pwd -W 2>/dev/null || pwd; } )

run() {  # run <cwd> <json-payload>
  ( cd "$1" && printf '%s' "$2" | $PY "$AG" hook-prompt )
}

check() {  # check <名称> <期望:yes|no> <子串> <cwd> <payload>
  local name="$1" want="$2" needle="$3" cwd="$4" payload="$5"
  local out; out=$(run "$cwd" "$payload" 2>&1)
  local got="no"; [ -n "$out" ] && got="yes"
  if [ "$got" != "$want" ]; then
    echo "FAIL  $name  期望=$want 实际=$got"; echo "      $out"; FAIL=$((FAIL+1)); return
  fi
  if [ "$want" = "yes" ] && [ -n "$needle" ]; then
    case "$out" in *"$needle"*) ;; *) echo "FAIL  $name  缺少子串「$needle」"; echo "      $out"; FAIL=$((FAIL+1)); return;; esac
  fi
  PASS=$((PASS+1)); echo "ok    $name"
}

rm -f "${TMPDIR:-/tmp}"/agile-hint-*.marker 2>/dev/null

W_EMPTY=$(w empty)
W_ACTIVE=$(w active)
W_BIG=$(w big)

P_PLAN='{"cwd":"'"$W_EMPTY"'","session_id":"s_plan","prompt":"帮我规划一下订单服务的模块划分"}'
P_CODE='{"cwd":"'"$W_EMPTY"'","session_id":"s_code","prompt":"这个空指针是哪里来的"}'
P_SKIP='{"cwd":"'"$W_EMPTY"'","session_id":"s_skip","prompt":"no-agile 帮我规划一下订单服务"}'
P_EMPTY='{"cwd":"'"$W_EMPTY"'","session_id":"s_empty","prompt":"   "}'
P_DUP='{"cwd":"'"$W_EMPTY"'","session_id":"s_dup","prompt":"帮我规划一下订单服务"}'
P_ACT='{"cwd":"'"$W_ACTIVE"'","session_id":"s1","prompt":"随便说点什么"}'
P_ACT_SKIP='{"cwd":"'"$W_ACTIVE"'","session_id":"s1","prompt":"no-agile 随便说点什么"}'

check "新项目 + 规划类 → 提示"        yes "这轮命中"      empty  "$P_PLAN"
check "新项目 + 执行类 → 静默"        no  ""              empty  "$P_CODE"
check "skip 关键词 → 静默"            no  ""              empty  "$P_SKIP"
check "空 prompt → 静默"              no  ""              empty  "$P_EMPTY"
check "同 session 第一轮提示"          yes "这轮命中"      empty  "$P_DUP"
check "同 session 第二轮静默"          no  ""              empty  "$P_DUP"

check "已启用项目 → 每轮状态"          yes "Backlog"      active "$P_ACT"
check "已启用项目 + skip → 静默"       no  ""             active "$P_ACT_SKIP"

# ── 边界：大小写、无 session_id、换会话、状态行有界 ──────────────────────────
P_UPPER='{"cwd":"'"$W_EMPTY"'","session_id":"s2","prompt":"SPRINT 怎么排"}'
check "大写 SPRINT 也命中"            yes "这轮命中"      empty  "$P_UPPER"

# 状态行不随项目规模膨胀：120 条池 + 100 个待回填，也只注入一行统计 + 至多 3 个名
P_BIG='{"cwd":"'"$W_BIG"'","session_id":"s_big","prompt":"继续"}'
out=$(run big "$P_BIG"); bytes=$(printf '%s' "$out" | wc -c)
if printf '%s' "$out" | grep -q '待回填 100 个' && [ "$bytes" -lt 1000 ]; then
  PASS=$((PASS+1)); echo "ok    状态行不随规模膨胀（${bytes}B）"
else
  FAIL=$((FAIL+1)); echo "FAIL  状态行随规模膨胀（${bytes}B）"; printf '%s\n' "$out"
fi

rm -f "${TMPDIR:-/tmp}"/agile-hint-*.marker 2>/dev/null
P_NOSID='{"cwd":"'"$W_EMPTY"'","prompt":"帮我看看 roadmap"}'
check "无 session_id 仍提示"          yes "这轮命中"      empty  "$P_NOSID"
check "无 session_id 当日第二次静默"   no  ""              empty  "$P_NOSID"

rm -f "${TMPDIR:-/tmp}"/agile-hint-*.marker 2>/dev/null
P_S1='{"cwd":"'"$W_EMPTY"'","session_id":"a1","prompt":"规划一下"}'
P_S2='{"cwd":"'"$W_EMPTY"'","session_id":"a2","prompt":"规划一下"}'
check "新会话重新提示"                yes "这轮命中"      empty  "$P_S1"
check "换 session_id 再提示一次"      yes "这轮命中"      empty  "$P_S2"

out=$( cd active && printf '%s' "$P_ACT" | sh "$PLUGIN/scripts/run-python.sh" hook-prompt )
case "$out" in *Backlog*) PASS=$((PASS+1)); echo "ok    wrapper 路径透传";; *) echo "FAIL  wrapper 路径透传: $out"; FAIL=$((FAIL+1));; esac

out=$( cd empty && printf '%s' "$P_PLAN" | PATH=/usr/bin sh "$PLUGIN/scripts/run-python.sh" hook-prompt )
code=$?
if [ -z "$out" ] && [ "$code" -eq 0 ]; then PASS=$((PASS+1)); echo "ok    无 python 时静默 exit 0"; else echo "FAIL  无 python 降级: out=$out code=$code"; FAIL=$((FAIL+1)); fi

echo "--- 已启用项目的完整输出 ---"
run active "$P_ACT"

echo
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
