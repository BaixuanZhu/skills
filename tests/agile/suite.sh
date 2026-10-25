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

# ── hooks.json 命令串直跑：宿主展开 ${CLAUDE_PLUGIN_ROOT} 后交给 shell 的就是它 ──
# 5.5.5 在 ZCode 上三 hook 全灭的根因是 command 型带 args（ZCode 只执行字符串本体、
# 静默丢弃 args），这里按两宿主的执行方式直跑命令串，并按 stdout 交集 schema 校验。
HOOKS="$PLUGIN/hooks/hooks.json"

hook_cmd() {  # hook_cmd <事件>：打印该事件 command 型条目的 command 串
  $PY - "$HOOKS" "$1" <<'PYEOF'
import json, sys
for entry in json.load(open(sys.argv[1], encoding="utf-8"))["hooks"][sys.argv[2]]:
    for hook in entry["hooks"]:
        if hook.get("type") == "command":
            print(hook["command"]); raise SystemExit(0)
raise SystemExit(1)
PYEOF
}

hooks_shape() {  # 形态守卫：args 复发 / timeout 不是秒 / 缺兜底都在这里拦
  $PY - "$HOOKS" <<'PYEOF'
import json, sys
problems = []
for event, entries in json.load(open(sys.argv[1], encoding="utf-8"))["hooks"].items():
    for e in entries:
        for h in e["hooks"]:
            if h.get("type") != "command":
                problems.append(f"{event}: type={h.get('type')} 不是 command")
            if "args" in h:
                problems.append(f"{event}: 带 args——ZCode 对 command 型静默丢弃 args（5.5.5 全灭根因）")
            t = h.get("timeout")
            if isinstance(t, bool) or not isinstance(t, int) or not 0 < t <= 60:
                problems.append(f"{event}: timeout 应为秒数(1~60)，当前 {t!r}")
            c = h.get("command", "")
            if "${CLAUDE_PLUGIN_ROOT}" not in c or "agile.py" not in c:
                problems.append(f"{event}: command 未指向插件内 agile.py")
            if "||" not in c:
                problems.append(f"{event}: 缺 python||python3 解释器兜底")
print("\n".join(problems)); raise SystemExit(1 if problems else 0)
PYEOF
}

hook_json_ok() {  # hook_json_ok <期望事件|->> <hook stdout>：按交集 schema 校验
  $PY - "$1" "$2" <<'PYEOF'
import json, sys
want, raw = sys.argv[1], sys.argv[2]
if want == "-":
    sys.exit(0 if not raw.strip() else 1)
if not raw.startswith("{"):  # ZCode：非 { 开头整段忽略 = 永不注入
    sys.exit(1)
obj = json.loads(raw)
top = {"hookSpecificOutput", "decision", "reason", "stopReason",
       "continue", "systemMessage", "suppressOutput", "additionalContext"}
hso = obj.get("hookSpecificOutput")
ok = set(obj) <= top and (
    hso is None or (set(hso) <= {"hookEventName", "additionalContext", "permissionDecision",
                                 "permissionDecisionReason", "updatedInput", "decision"}
                    and hso.get("hookEventName") == want))
sys.exit(0 if ok else 1)
PYEOF
}

expand_for() {  # expand_for <posix|win> <模板>：模拟宿主展开插件根变量
  local root
  if [ "$1" = win ]; then root=$(w ../../plugins/agile); else root=$PLUGIN; fi
  printf '%s' "$2" | sed "s|\${CLAUDE_PLUGIN_ROOT}|$root|g"
}

if hooks_shape; then PASS=$((PASS+1)); echo "ok    hooks.json 形态（无 args / 秒 timeout / 带兜底）"
else FAIL=$((FAIL+1)); echo "FAIL  hooks.json 形态"; hooks_shape; fi

S_SESSION=$(expand_for posix "$(hook_cmd SessionStart)")
out=$( cd active && printf '%s' "$P_ACT" | sh -c "$S_SESSION" ); code=$?
if [ "$code" -eq 0 ] && hook_json_ok SessionStart "$out" && printf '%s' "$out" | grep -q agile-state; then
  PASS=$((PASS+1)); echo "ok    SessionStart 命令串（sh）注入状态块"
else FAIL=$((FAIL+1)); echo "FAIL  SessionStart 命令串（sh）: code=$code out=$out"; fi

# 静默用例的 payload 必须指向 empty 本身：脚本以 payload 的 cwd 为准（宿主同样传项目目录）
P_SILENT='{"cwd":"'"$W_EMPTY"'","session_id":"s_silent"}'
out=$( cd empty && printf '%s' "$P_SILENT" | sh -c "$S_SESSION" ); code=$?
if [ "$code" -eq 0 ] && hook_json_ok - "$out"; then
  PASS=$((PASS+1)); echo "ok    非 agile 项目命令串（sh）静默"
else FAIL=$((FAIL+1)); echo "FAIL  非 agile 项目命令串（sh）: code=$code out=$out"; fi

S_POST=$(expand_for posix "$(hook_cmd PostToolUse)")
TP=$(mktemp -d); mkdir -p "$TP/agile-docs"
printf '{oops' > "$TP/agile-docs/backlog.json"
W_TP=$(w "$TP")
out=$( cd "$TP" && printf '{"cwd":"%s","tool_input":{"file_path":"%s/agile-docs/backlog.json"}}' "$W_TP" "$W_TP" | sh -c "$S_POST" ); code=$?
blocked=$(printf '%s' "$out" | $PY -c 'import json,sys; o=json.load(sys.stdin); print("yes" if o.get("decision")=="block" else "no")' 2>/dev/null)
if [ "$code" -eq 0 ] && [ "$blocked" = yes ] && printf '%s' "$out" | grep -q '不是合法 JSON'; then
  PASS=$((PASS+1)); echo "ok    坏 json 写入 → decision:block + exit 0（sh）"
else FAIL=$((FAIL+1)); echo "FAIL  坏 json 写入（sh）: code=$code blocked=$blocked out=$out"; fi
rm -rf "$TP"

# Windows 宿主默认 cmd.exe，且以「单个 verbatim argv」直传命令串（cmd /d /s /c "…"）。
# 从 Git Bash 直接调 cmd 会被 MSYS 把内层引号转义坏（假阳性），必须用 node 按宿主
# 同款 spawn 复刻；命令串与 payload 走环境变量，不经过 argv。
if command -v node >/dev/null 2>&1 && command -v cmd >/dev/null 2>&1; then
  run_cmd_host() {  # run_cmd_host <命令串> <payload>：宿主同款执行，stdout 原样、退出码透传
    AGILE_HOOK_CMD="$1" AGILE_HOOK_STDIN="$2" node -e '
const { spawnSync } = require("child_process");
const r = spawnSync(process.env.ComSpec || "cmd.exe",
  ["/d", "/s", "/c", "\"" + process.env.AGILE_HOOK_CMD + "\""],
  { input: process.env.AGILE_HOOK_STDIN, windowsVerbatimArguments: true });
process.stdout.write(r.stdout || "");
process.exit(r.status == null ? 1 : r.status);'
  }

  W_PROMPT=$(expand_for win "$(hook_cmd UserPromptSubmit)")
  out=$( cd active && run_cmd_host "$W_PROMPT" "$P_ACT" ); code=$?
  if [ "$code" -eq 0 ] && hook_json_ok UserPromptSubmit "$out" && printf '%s' "$out" | grep -q Backlog; then
    PASS=$((PASS+1)); echo "ok    UserPromptSubmit 命令串（cmd/宿主形态）注入状态块"
  else FAIL=$((FAIL+1)); echo "FAIL  UserPromptSubmit 命令串（cmd/宿主形态）: code=$code out=$out"; fi

  W_SESSION=$(expand_for win "$(hook_cmd SessionStart)")
  out=$( cd empty && run_cmd_host "$W_SESSION" "$P_SILENT" ); code=$?
  if [ "$code" -eq 0 ] && hook_json_ok - "$out"; then
    PASS=$((PASS+1)); echo "ok    非 agile 项目命令串（cmd/宿主形态）静默"
  else FAIL=$((FAIL+1)); echo "FAIL  非 agile 项目命令串（cmd/宿主形态）: code=$code out=$out"; fi
fi

echo "--- 已启用项目的完整输出 ---"
run active "$P_ACT"

echo
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
