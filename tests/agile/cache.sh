#!/usr/bin/env bash
# 长期待办日缓存专项回归：每条都对应缓存引入后才可能出现的故障形态。
# 用法：bash tests/agile/cache.sh（解释器叫 python3 的环境：PY=python3 …）
#
# 覆盖：首算一次后续命中 / 负缓存 / 跨日重算 / mtime 指纹失效（内容不变）/
# reviewed_at 更新与外部改写 / 损坏与版本不符降级 / marker 原子领取（线程 + 进程）/
# no-agile 不建缓存 / SessionStart 暖缓存不领额度 / PostToolUse 主动失效不删 marker /
# review/stats 始终读实时文件（CLI 不走缓存）。
set -u
cd "$(dirname "$0")"
PLUGIN="$(cd ../../plugins/agile && pwd)"
SCRIPTS="$PLUGIN/scripts"
AG="$SCRIPTS/agile.py"
PY="${PY:-python}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
PASS=0; FAIL=0

w() ( cd "$1" && { pwd -W 2>/dev/null || pwd; } )

check() { # check <名称> <期望> <实际>
  if [ "$2" = "$3" ]; then PASS=$((PASS + 1)); printf 'ok    %s\n' "$1"
  else FAIL=$((FAIL + 1)); printf 'FAIL  %s\n        期望: %s\n        实际: %s\n' "$1" "$2" "$3"; fi
}

mkproj() { # mkproj <名>：复制 aging fixture → $WORK/<名>，返回 Windows 路径
  rm -rf "$WORK/$1"; cp -r aging "$WORK/$1"; w "$WORK/$1"
}

reset_state() { # reset_state <windows 根> <all|marker>：all=快照+marker，marker=只清额度
  (cd "$SCRIPTS" && "$PY" -c '
import sys
from pathlib import Path
import agile
root, mode = Path(sys.argv[1]), sys.argv[2]
targets = [agile.review_marker(root)] if mode == "marker" else [
    agile.age_cache_path(root), agile.review_marker(root)]
for p in targets:
    Path(p).unlink(missing_ok=True)
' "$1" "$2")
}

state_bool() { # state_bool <windows 根> <cache|marker> → true/false
  (cd "$SCRIPTS" && "$PY" -c '
import sys
from pathlib import Path
import agile
root = Path(sys.argv[1])
print(str(agile.age_cache_path(root).exists() if sys.argv[2] == "cache"
          else agile.review_marker(root).exists()).lower())
' "$1" "$2")
}

# ── 进程内场景：固定 today，给 collect_backlog_age 挂数计数 ────────────────────
W1=$(mkproj snap)
W2="$WORK/neg"; mkdir -p "$W2/agile-docs"
cat > "$W2/agile-docs/backlog.json" <<'JSON'
{"schema": 1, "phases": [{"id": 1, "title": "新池", "items": [
  {"id": "F-070", "title": "近期条目", "type": "功能", "points": 2,
   "priority": "Should", "status": "待办", "confirmed": true, "created_at": "2026-10-15"}
]}]}
JSON
W3="$WORK/none"; mkdir -p "$W3"   # 有目录但没有 backlog：快照应为 None

INPROC="$(cd "$SCRIPTS" && "$PY" - "$W1" "$W2" "$W3" <<'PY'
import json, os, sys, threading
from datetime import date
from pathlib import Path
import agile

proj, neg, none_root = (Path(a) for a in sys.argv[1:4])
backlog = proj / "agile-docs" / "backlog.json"

calls = []
real_collect = agile.collect_backlog_age
def counting(data, sprints, today):
    calls.append(today.isoformat())
    return real_collect(data, sprints, today)
agile.collect_backlog_age = counting

results = []
def case(name, ok):
    results.append(f"{name}={ok!s}")

def reset():
    agile.age_cache_path(proj).unlink(missing_ok=True)
    agile.review_marker(proj).unlink(missing_ok=True)

# A 首算恰好一次，后续同日命中；明细行与 review 清单同格式
reset()
snap_a1 = agile.age_snapshot(proj, date(2026, 11, 2))
snap_a2 = agile.age_snapshot(proj, date(2026, 11, 2))
case("A_compute_once", len(calls) == 1 and snap_a1 == snap_a2 and snap_a1["due_count"] == 1)
case("A_notice_render",
     snap_a1["notice_items"] == ["- F-060 早期立项的 Could 条目｜Could｜立项 2497 天｜从未纳入 Sprint"])

# B 负缓存：无长期待办也写缓存，第二趟不再计算
calls_before = len(calls)
snap_b1 = agile.age_snapshot(neg, date(2026, 11, 2))
snap_b2 = agile.age_snapshot(neg, date(2026, 11, 2))
case("B_negative_cache", snap_b1 == snap_b2 and snap_b1["summary"] == []
     and snap_b1["due_count"] == 0
     and calls[calls_before:] == ["2026-11-02"]   # 两次调用只算一次
     and agile.age_cache_path(neg).exists())

# C 跨日：缓存按自然日失效，年龄 +1；切回当日再算一次
snap_c1 = agile.age_snapshot(proj, date(2026, 11, 3))
snap_c2 = agile.age_snapshot(proj, date(2026, 11, 2))
case("C_cross_day", calls.count("2026-11-03") == 1 and "2498" in snap_c1["notice_items"][0]
     and "2497" in snap_c2["notice_items"][0] and calls.count("2026-11-02") == 3)

# D mtime 指纹失效：内容一字不改，只动 mtime 也必须重算，结果不变
stat = backlog.stat()
os.utime(backlog, ns=(stat.st_atime_ns + 10**9, stat.st_mtime_ns + 10**9))
snap_d = agile.age_snapshot(proj, date(2026, 11, 2))
case("D_mtime_fingerprint", calls.count("2026-11-02") == 4 and snap_d == snap_c2)

# E 用户确认复核后：due 归零 → 负缓存（长期未完成仍在，只是不提醒）
data = json.loads(backlog.read_text(encoding="utf-8"))
data["phases"][0]["items"][0]["last_reviewed_at"] = "2026-11-01"
backlog.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
snap_e = agile.age_snapshot(proj, date(2026, 11, 2))
agile.age_snapshot(proj, date(2026, 11, 2))
case("E_reviewed_updates", snap_e["due_count"] == 0 and snap_e["notice_items"] == []
     and snap_e["summary"] == ["长期未完成 1 条（≥30 天，最久 2497 天；待复核 0 条）"]
     and calls.count("2026-11-02") == 5)  # 第二次调用命中负缓存，不再计

# F 外部改写成已完成 → 指纹变化重算，汇总行消失
data["phases"][0]["items"][0]["status"] = "已完成"
backlog.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
snap_f = agile.age_snapshot(proj, date(2026, 11, 2))
case("F_external_edit", snap_f["summary"] == [] and snap_f["due_count"] == 0)

# G 损坏 / 版本不符 / 字段类型错：一律当未命中，重算并自愈
cache = agile.age_cache_path(proj)
cache.write_text("{oops", encoding="utf-8")
snap_g1 = agile.age_snapshot(proj, date(2026, 11, 2))
case("G_corrupt_fail_open", snap_g1["due_count"] == 0
     and json.loads(cache.read_text(encoding="utf-8"))["version"] == agile.AGE_CACHE_VERSION)
body = json.loads(cache.read_text(encoding="utf-8"))
body["version"] = agile.AGE_CACHE_VERSION + 99
cache.write_text(json.dumps(body), encoding="utf-8")
snap_g2 = agile.age_snapshot(proj, date(2026, 11, 2))
body["version"] = agile.AGE_CACHE_VERSION
body["summary"] = 3   # 非字符串数组：load 层的类型守卫要拒绝
cache.write_text(json.dumps(body), encoding="utf-8")
snap_g3 = agile.age_snapshot(proj, date(2026, 11, 2))
case("G_version_and_type_guard", snap_g2 == snap_g3 == snap_f)

# M marker 原子领取：单进程二次领取失败；8 线程并发只有一个展开提醒
marker = agile.review_marker(proj)
marker.unlink(missing_ok=True)
first = agile.claim_day_marker(marker)
second = agile.claim_day_marker(marker)
case("M_claim_once", first and not second)
marker.unlink(missing_ok=True)
snapshot_stub = {"summary": [], "due_count": 2, "notice_items": ["- x", "- y"]}
notices = []
def worker():
    notices.append(agile.claim_review_notice(proj, {"review": "b"}, snapshot_stub))
threads = [threading.Thread(target=worker) for _ in range(8)]
for t in threads: t.start()
for t in threads: t.join()
case("M_threads_single_notice", sum(1 for n in notices if n) == 1)

# N 没有 backlog 的目录：指纹拿不到 → 快照 None（不写缓存、不报错）
case("N_no_backlog_none", agile.age_snapshot(none_root, date(2026, 11, 2)) is None
     and agile.age_fingerprint(none_root) is None)

print("\n".join(results))
PY
)"
for line in $INPROC; do
  key="${line%%=*}"; val="${line#*=}"
  val="${val%$'\r'}"   # Windows python 往管道写 CRLF，token 尾巴会带 \r
  check "$key" "True" "$val"
done

# ── no-agile：本轮退出在缓存读取与计算之前，不留任何痕迹 ──────────────────────
W4=$(mkproj noagile)
reset_state "$W4" all
P_NOAGILE='{"cwd":"'"$W4"'","session_id":"s_noagile","prompt":"no-agile 继续"}'
out=$( cd "$WORK/noagile" && printf '%s' "$P_NOAGILE" | $PY "$AG" hook-prompt )
check "no-agile 无输出" "" "$out"
check "no-agile 不建快照" "false" "$(state_bool "$W4" cache)"
check "no-agile 不领 marker" "false" "$(state_bool "$W4" marker)"

# ── SessionStart 暖缓存但不领额度；首次发言展开；PostToolUse 主动失效 ─────────
W5=$(mkproj flow)
reset_state "$W5" all
P_FLOW='{"cwd":"'"$W5"'","session_id":"s_flow","prompt":"继续"}'
out=$( cd "$WORK/flow" && printf '{"cwd":"%s","session_id":"s_flow"}' "$W5" | $PY "$AG" hook-session )
case "$out" in
  *长期未完成*'<agile-review>'*) check "SessionStart 不展开明细" "" "展开了";;
  *长期未完成*) check "SessionStart 只有汇总" "1" "1";;
  *) check "SessionStart 只有汇总" "汇总" "输出缺长期未完成: $out";;
esac
check "SessionStart 已暖快照" "true" "$(state_bool "$W5" cache)"
check "SessionStart 未领额度" "false" "$(state_bool "$W5" marker)"

out=$( cd "$WORK/flow" && printf '%s' "$P_FLOW" | $PY "$AG" hook-prompt )
case "$out" in *'<agile-review>'*'F-060'*) check "首次发言展开提醒" "1" "1";;
  *) check "首次发言展开提醒" "F-060" "缺失: $out";; esac

# 写 backlog → 快照删除、marker 保留（同日不因文件变化再次展开）；下一轮重建快照
out=$( cd "$WORK/flow" && printf '{"cwd":"%s","tool_input":{"file_path":"%s/agile-docs/backlog.json"}}' "$W5" "$W5" | $PY "$AG" hook-post-write )
check "backlog 写后校验无输出" "" "$out"
check "写后快照被删" "false" "$(state_bool "$W5" cache)"
check "写后 marker 保留" "true" "$(state_bool "$W5" marker)"
out=$( cd "$WORK/flow" && printf '%s' "$P_FLOW" | $PY "$AG" hook-prompt )
case "$out" in *'<agile-review>'*) check "同日失效后不重复展开" "" "展开了";;
  *) check "同日失效后不重复展开" "1" "1";; esac
check "下一轮重建快照" "true" "$(state_bool "$W5" cache)"

# 写 Sprint 文件同样失效
out=$( cd "$WORK/flow" && printf '{"cwd":"%s","tool_input":{"file_path":"%s/sprints/sprint-001-20200101.md"}}' "$W5" "$W5" | $PY "$AG" hook-post-write )
check "Sprint 写后快照被删" "false" "$(state_bool "$W5" cache)"

# ── CLI 永远读实时文件；hook 侧外部改写由指纹兜底 ────────────────────────────
W6=$(mkproj live)
reset_state "$W6" all
P_LIVE='{"cwd":"'"$W6"'","session_id":"s_live","prompt":"继续"}'
out=$( cd "$WORK/live" && printf '%s' "$P_LIVE" | $PY "$AG" hook-prompt )
case "$out" in *'<agile-review>'*) check "live 基线先展开一次" "1" "1";;
  *) check "live 基线先展开一次" "review" "缺失: $out";; esac
(cd "$SCRIPTS" && "$PY" -c '
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "agile-docs" / "backlog.json"
d = json.loads(p.read_text(encoding="utf-8"))
d["phases"][0]["items"][0]["status"] = "已完成"
p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
' "$W6")   # 外部改写：不走 PostToolUse，快照只能靠指纹发现
out=$( cd "$WORK/live" && $PY "$AG" review . )
case "$out" in *F-060*) check "review 读实时文件" "" "仍在列 F-060";;
  *) check "review 读实时文件" "1" "1";; esac
out=$( cd "$WORK/live" && $PY "$AG" stats . )
case "$out" in *长期未完成*) check "stats 读实时文件" "" "仍有长期未完成";;
  *) check "stats 读实时文件" "1" "1";; esac
check "外部改写后旧快照仍在" "true" "$(state_bool "$W6" cache)"
reset_state "$W6" marker   # 只清提醒额度：旧快照保留，hook 必须靠指纹弃用它
out=$( cd "$WORK/live" && printf '%s' "$P_LIVE" | $PY "$AG" hook-prompt )
case "$out" in
  *'<agile-review>'*) check "hook 侧指纹兜底" "" "展开了旧明细";;
  *长期未完成*) check "hook 侧指纹兜底" "状态行同步消失" "状态行仍带长期未完成: $out";;
  *) check "hook 侧指纹兜底" "1" "1";;
esac

# ── 进程级并发：4 个 hook 同时抢当日额度，只有一个展开 ───────────────────────
W7=$(mkproj race)
reset_state "$W7" all
for i in 1 2 3 4; do
  ( cd "$WORK/race" && printf '{"cwd":"%s","session_id":"race-%s","prompt":"继续"}' "$W7" "$i" \
      | $PY "$AG" hook-prompt > "$WORK/race.$i.out" ) &
done
wait
notices=$(cat "$WORK"/race.*.out | grep -c '<agile-review>')
states=$(cat "$WORK"/race.*.out | grep -c 'Backlog')
check "并发只有一个展开提醒" "1" "$notices"
check "并发四个都注入状态" "4" "$states"

printf '\nPASS=%d FAIL=%d\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
