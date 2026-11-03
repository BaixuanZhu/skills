#!/bin/sh
# agile.py 代码质量回归：每一条都对应一个曾经真实出错的点。
# 用法：sh tests/agile/regress.sh（解释器叫 python3 的环境：PY=python3 sh …）
#
# 注意：所有 python 片段都用相对路径 + 先 cd 进目标目录。Git Bash 里
# `/i/...`、`/tmp/...` 这类 POSIX 路径写在 `-c` 程序内部不会被翻译，
# Windows 解释器找不到（这正是本脚本第一版自己踩的坑）。
set -u
PLUGIN="$(cd "$(dirname "$0")/../../plugins/agile" && pwd)"
PY="${PY:-python}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
PASS=0
FAIL=0

check() { # $1=名称 $2=期望 $3=实际
  if [ "$2" = "$3" ]; then PASS=$((PASS + 1)); printf 'ok    %s\n' "$1"
  else FAIL=$((FAIL + 1)); printf 'FAIL  %s\n        期望: %s\n        实际: %s\n' "$1" "$2" "$3"; fi
}

run() { (cd "$WORK" && "$PY" "$PLUGIN/scripts/agile.py" "$@"); }

# ① 两位数 Sprint 序号：字符串排序会让「当前 Sprint」永远停在 9
mkdir -p "$WORK/agile-docs/sprints"
for n in 1 2 9 10; do
  printf -- '- **状态**: 已关闭\n- **周期**: 2026-W0%s\n' "$n" > "$WORK/agile-docs/sprints/sprint-$n.md"
done
printf -- '- **状态**: 规划完成\n- **周期**: 2026-W99\n' > "$WORK/agile-docs/sprints/sprint-12.md"
BRIEF="$(run brief)"
check "两位数序号取到最后一个 Sprint" "1" "$(printf '%s' "$BRIEF" | grep -c 'Sprint 12 规划完成')"
check "不会被 sprint-9 顶替" "0" "$(printf '%s' "$BRIEF" | grep -c 'Sprint 9 ')"

# ② 合法 backlog.json 地基（migrate 已删，fixture 直接铺 json；标题带 | 验证竖线在 json 里天然无害）
cat > "$WORK/agile-docs/backlog.json" <<'JSON'
{
  "schema": 1,
  "phases": [
    {
      "id": 1,
      "title": "基础",
      "items": [
        {"id": "T-001", "title": "支持 A | B 双写", "type": "技术", "points": 3,
         "priority": "Must", "status": "待办", "confirmed": false}
      ]
    }
  ]
}
JSON
check "stats 全量重算" "1" "$(run stats | grep -c '条目：1 条 / 3 点')"

# ③ 只有 ID 没有标题的 Sprint 清单行不能被丢掉（否则对账网少一个洞）
check "只写 ID 的清单行仍参与对账" "[('T-001', None)]" \
  "$(cd "$PLUGIN/scripts" && "$PY" -c "
import agile; print(agile.parse_sprint_items('- T-001\n'))")"

# ④ 未引用的函数：重构后不应该再出现
check "无未引用函数" "无" \
  "$(cd "$PLUGIN/scripts" && "$PY" -c "
import ast,collections
tree=ast.parse(open('agile.py',encoding='utf-8').read())
defs={n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)}
used=collections.Counter(n.id for n in ast.walk(tree) if isinstance(n,ast.Name))
print(', '.join(sorted(d for d in defs if used[d]==0)) or '无')")"

# ⑤ CLI 冒烟：合规项目三个命令都要 exit 0
check "check  退出码" "0" "$(run check >/dev/null 2>&1; echo $?)"
check "stats  退出码" "0" "$(run stats >/dev/null 2>&1; echo $?)"
check "review 退出码（存量无日期也正常）" "0" "$(run review >/dev/null 2>&1; echo $?)"

# ⑥ 渲染退役后：遗留 md 只提示可删，不算 problem（check 仍 exit 0）
printf '旧渲染产物残留\n' > "$WORK/agile-docs/PRODUCT-BACKLOG.md"
check "遗留 md 不算问题" "0" "$(run check >/dev/null 2>&1; echo $?)"
check "遗留 md 提示可删" "1" "$(run check 2>&1 | grep -c '已不再生成')"

# ⑦ 非法结构必须 exit 1，不能静默通过
(cd "$WORK" && "$PY" -c "
import json
p='agile-docs/backlog.json'; d=json.load(open(p,encoding='utf-8'))
d['phases'][0]['items'][0]['points']=0
json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False)")
check "points=0 被判错" "1" "$(run check >/dev/null 2>&1; echo $?)"

# ⑧ 布尔是 int 的子类：`"points": true` 不能被当成 1 点放行
(cd "$WORK" && "$PY" -c "
import json
p='agile-docs/backlog.json'; d=json.load(open(p,encoding='utf-8'))
d['phases'][0]['items'][0]['points']=True
json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False)")
check "points=true 被判错" "1" "$(run check >/dev/null 2>&1; echo $?)"
check "报的是点数不是斐波那契" "1" "$(run check 2>&1 | grep -c 'points 必须是正整数')"

# ⑨ 键值行拆分：两种冒号比位置、不比固定优先级。
#    闭环注记把状态行写成 `- 状态: 已关闭（执行结果来源：…）`，旧实现先按全角
#    partition，键被切成「状态: 已关闭（执行结果来源」，白名单拒收后整行丢弃。
check "半角分隔 + 值内全角冒号" "状态|:|已关闭（执行结果来源：x）" \
  "$(cd "$PLUGIN/scripts" && PYTHONIOENCODING=utf-8 "$PY" -c "
import agile; print('|'.join(agile.split_kv('状态: 已关闭（执行结果来源：x）')))")"
check "全角分隔" "状态|：|已规划" \
  "$(cd "$PLUGIN/scripts" && PYTHONIOENCODING=utf-8 "$PY" -c "
import agile; print('|'.join(agile.split_kv('状态：已规划')))")"
check "周期行" "周期|:|2026-10-20 ~ 2026-10-27" \
  "$(cd "$PLUGIN/scripts" && PYTHONIOENCODING=utf-8 "$PY" -c "
import agile; print('|'.join(agile.split_kv('周期: 2026-10-20 ~ 2026-10-27')))")"
check "无冒号行 sep 为空" "说明||" \
  "$(cd "$PLUGIN/scripts" && PYTHONIOENCODING=utf-8 "$PY" -c "
import agile; print('|'.join(agile.split_kv('说明')))")"

# ⑩ split_kv 的另一个调用方：回填文件 feedback.note 值内含全角冒号时，
#    旧实现把键切成 `note: "…需产品确认`，note 静默丢失且 inspect_done 不查它。
check "feedback.note 值内全角冒号不丢" "配额不足，需产品确认：降级方案" \
  "$(cd "$PLUGIN/scripts" && PYTHONIOENCODING=utf-8 "$PY" -c "
import agile
t = 'feedback:\n  - item: T-001\n    type: reason\n    note: \"配额不足，需产品确认：降级方案\"\n'
print(agile.parse_done(t)['feedback'][0].get('note', ''))")"

# ⑪ 端到端：已闭环 Sprint 必须判「已关闭」——状态词丢掉会让 active 判定失效、
#    brief 永远停在「Sprint 进行中」。两场景各验一次（有进行中 / 只剩已关闭）。
CLOSED="$WORK/closed"
mkdir -p "$CLOSED/sprints" "$CLOSED/agile-docs"
cat > "$CLOSED/sprints/sprint-071-20261027.md" <<'MD'
# Sprint: 已闭环

- 文件名: sprint-071-20261027
- 状态: 已关闭（执行结果来源：sprints/sprint-071-20261027.done.yaml，闭环同步后改名 .done.processed.yaml 留痕）
- 周期: 2026-10-20 ~ 2026-10-27
MD
cat > "$CLOSED/sprints/sprint-072-20261028.md" <<'MD'
# Sprint: 进行中

- 文件名: sprint-072-20261028
- 状态: 规划完成
- 周期: 2026-10-28 ~ 2026-11-03
MD
cp "$WORK/agile-docs/backlog.json" "$CLOSED/agile-docs/backlog.json"

brief_at() { (cd "$1" && "$PY" "$PLUGIN/scripts/agile.py" brief . 2>&1); }

WITH_OPEN="$(brief_at "$CLOSED")"
check "有进行中 Sprint 时判 active" "1" "$(printf '%s' "$WITH_OPEN" | grep -c '^阶段：active')"
check "取最新 Sprint 的状态" "1" "$(printf '%s' "$WITH_OPEN" | grep -cF 'Sprint 072 规划完成 (2026-10-28 ~ 2026-11-03)')"

mv "$CLOSED/sprints/sprint-072-20261028.md" "$CLOSED/sprint-072.moved"
ONLY_CLOSED="$(brief_at "$CLOSED")"
check "只剩已关闭 Sprint 时判 sprint" "1" "$(printf '%s' "$ONLY_CLOSED" | grep -c '^阶段：sprint')"
check "已关闭 Sprint 显示状态词" "1" "$(printf '%s' "$ONLY_CLOSED" | grep -cF 'Sprint 071 已关闭 (2026-10-20 ~ 2026-10-27)')"
check "状态行不带闭环注记" "0" "$(printf '%s' "$ONLY_CLOSED" | grep -c '执行结果来源')"
mv "$CLOSED/sprint-072.moved" "$CLOSED/sprints/sprint-072-20261028.md"

# ⑫ 状态三态只在一处判定：closed / planned / unknown
check "闭环注记判 closed" "closed" \
  "$(cd "$PLUGIN/scripts" && PYTHONIOENCODING=utf-8 "$PY" -c "
import agile; print(agile.sprint_status({'状态': '已关闭（执行结果来源：x）'}))")"
check "规划完成判 planned" "planned" \
  "$(cd "$PLUGIN/scripts" && PYTHONIOENCODING=utf-8 "$PY" -c "
import agile; print(agile.sprint_status({'状态': '规划完成'}))")"
check "写岔判 unknown" "unknown" \
  "$(cd "$PLUGIN/scripts" && PYTHONIOENCODING=utf-8 "$PY" -c "
import agile; print(agile.sprint_status({'状态': '已完成'}))")"

# ⑬ 文件头三种写法并存（schema 说 YAML-style / 模板写列表符 / 早期 fixture 写裸键值），
#    只认列表符会让裸键值文件的状态从来没被读到——恰好「解析不到 → 默认 active」蒙对。
check "裸键值也解析" "规划完成|2026-10-20 ~ 2026-11-02" \
  "$(cd "$PLUGIN/scripts" && PYTHONIOENCODING=utf-8 "$PY" -c "
import agile
m = agile.parse_sprint_meta('状态: 规划完成\n周期: 2026-10-20 ~ 2026-11-02\n')
print(m.get('状态', '') + '|' + m.get('周期', ''))")"

# ⑭ 序号只解析一次：排序按 NNN，不按末段日期。命名混用时 sprint-071-20261027 的
#    末段（20261027）比 sprint-072 大，旧实现会把旧 Sprint 当成最新的。
MIX="$WORK/mixed"; mkdir -p "$MIX/sprints" "$MIX/agile-docs"
cp "$WORK/agile-docs/backlog.json" "$MIX/agile-docs/backlog.json"
printf -- '- 状态: 已关闭\n- 周期: 2026-10-20 ~ 2026-10-27\n' > "$MIX/sprints/sprint-071-20261027.md"
printf -- '- 状态: 规划完成\n- 周期: 2026-10-28 ~ 2026-11-03\n' > "$MIX/sprints/sprint-072.md"
check "命名混用按序号取最新" "1" "$(brief_at "$MIX" | grep -cF 'Sprint 072 规划完成')"

# ⑮ 未知状态不静默降级：仍按 active 计（保守，不误判关闭），但状态行必须显式标注
UNK="$WORK/unknown"; mkdir -p "$UNK/sprints" "$UNK/agile-docs"
cp "$WORK/agile-docs/backlog.json" "$UNK/agile-docs/backlog.json"
printf -- '- 状态: 已完成\n- 周期: 2026-11-04 ~ 2026-11-10\n' > "$UNK/sprints/sprint-073-20261104.md"
UNK_BRIEF="$(brief_at "$UNK")"
check "未知状态仍判 active" "1" "$(printf '%s' "$UNK_BRIEF" | grep -c '^阶段：active')"
check "未知状态显示状态未识别" "1" "$(printf '%s' "$UNK_BRIEF" | grep -cF 'Sprint 073 状态未识别')"

# ⑯ 契约变成可执行断言：check 报出写岔的状态词，且不依赖 backlog.json 是否存在
check "check 报 Sprint 头即退出 1" "1" "$(cd "$UNK" && "$PY" "$PLUGIN/scripts/agile.py" check . >/dev/null 2>&1; echo $?)"
check "报文件名与实际取值" "1" \
  "$(cd "$UNK" && PYTHONIOENCODING=utf-8 "$PY" "$PLUGIN/scripts/agile.py" check . 2>&1 | grep -cF 'sprint-073-20261104.md: 状态「已完成」')"
rm "$UNK/agile-docs/backlog.json"
check "backlog 缺失仍报 Sprint 头" "1" \
  "$(cd "$UNK" && PYTHONIOENCODING=utf-8 "$PY" "$PLUGIN/scripts/agile.py" check . 2>&1 | grep -cF 'sprint-073-20261104.md')"

# ⑰ 长期待办：固定 today 验证 29/30/31 天、Could 两月、复核间隔、活跃 Sprint 排除。
AGING_RESULT="$(cd "$PLUGIN/scripts" && "$PY" - <<'PY'
from datetime import date
import agile

def item(ident, created=None, status="待办", priority="Could", reviewed=None):
    row = {"id": ident, "title": ident, "type": "功能", "points": 1,
           "priority": priority, "status": status, "confirmed": True}
    if created is not None:
        row["created_at"] = created
    if reviewed is not None:
        row["last_reviewed_at"] = reviewed
    return row

items = [
    item("F-001", "2026-08-03"),
    item("F-002", "2026-10-03", priority="Must"),
    item("F-003", "2026-10-04", priority="Should"),
    item("F-004", "2026-08-01", reviewed="2026-10-15"),
    item("F-005", "2026-08-01", reviewed="2026-10-03"),
    item("F-006", "2026-08-01", status="已完成"),
    item("F-007", "2026-08-01", status="已撤回"),
    item("F-008", "2026-08-01"),
    item("F-009"),
    item("F-010", "2026/08/01"),
    item("F-011", "2026-11-03"),
    item("F-013", "2026-10-02"),
]
data = {"phases": [{"id": 1, "title": "测试", "items": items}]}
sprints = [
    (None, "sprint-001", {"状态": "已关闭"}, [("F-002", 1)]),
    (None, "sprint-002", {"状态": "规划完成"}, [("F-008", 1)]),
]
today = date(2026, 11, 2)
report = agile.collect_backlog_age(data, sprints, today)
print("aged=" + ",".join(row["id"] for row in report["aged"])
      + " due=" + ",".join(row["id"] for row in report["due"])
      + " unknown=" + ",".join(row["id"] for row in report["unknown"]))
by_id = {row["id"]: row for row in report["aged"]}
print("flags=" + "|".join([
    str(by_id["F-004"]["age"] == 93 and not by_id["F-004"]["due"]),
    str(by_id["F-005"]["due"]),
    str(by_id["F-001"]["age"] == 91 and by_id["F-001"]["due"]),
    str(by_id["F-002"]["ever_planned"] and not by_id["F-001"]["ever_planned"]),
]))
errors, _warnings = agile.validate(data, today)
bad = item("F-012", "2026-10-01", reviewed="2026-09-01")
bad_errors, _ = agile.validate({"phases": [{"id": 1, "title": "测试", "items": [bad]}]}, today)
future_review = item("F-014", "2026-08-01", reviewed="2026-11-03")
future_report = agile.collect_backlog_age(
    {"phases": [{"id": 1, "title": "测试", "items": [future_review]}]}, [], today)
print("validation=" + "|".join([
    str(any("F-010" in line and "YYYY-MM-DD" in line for line in errors)),
    str(any("F-011" in line and "不能晚于今天" in line for line in errors)),
    str(not any(line.startswith("F-009") for line in errors)),
    str(any("不能早于 created_at" in line for line in bad_errors)),
    str(len(future_report["due"]) == 1),
]))
rendered = "\n".join(agile.render_review_lines(report))
print("render=" + str("2026-10-15｜近期已复核" in rendered and "年龄只是复核信号" in rendered))
PY
)"
check "长期待办筛选、排序与未知日期分组" \
  "aged=F-004,F-005,F-001,F-013,F-002 due=F-005,F-001,F-013,F-002 unknown=F-009,F-010,F-011" \
  "$(printf '%s\n' "$AGING_RESULT" | grep '^aged=')"
check "复核不改年龄且 Sprint 历史只作标注" \
  "flags=True|True|True|True" "$(printf '%s\n' "$AGING_RESULT" | grep '^flags=')"
check "日期非法报错且不能抑制复核提醒" \
  "validation=True|True|True|True|True" "$(printf '%s\n' "$AGING_RESULT" | grep '^validation=')"
check "review 完整清单保留复核语义" "render=True" "$(printf '%s\n' "$AGING_RESULT" | grep '^render=')"

# ⑱ Sprint 归档：archive/ 不进任何扫描（状态行/active/指纹全看不见），「曾纳入」
#     只剩 planned_sprints 戳记兜底；移动改指纹强制重算；迟到的 .done.yaml 对已
#     归档 Sprint 仍能进 backfill 闭环。固定 today，全部进程内断言 + 两条 CLI 断言。
ARCH_OUT="$(cd "$PLUGIN/scripts" && PYTHONIOENCODING=utf-8 "$PY" - <<'PY' | tr -d '\r'
import json, shutil, tempfile
from datetime import date
from pathlib import Path
import agile

root = Path(tempfile.mkdtemp())
docs = root / "agile-docs"
live = root / "sprints"
docs.mkdir()
(live / "archive").mkdir(parents=True)
backlog = {"schema": 1, "phases": [{"id": 1, "title": "归档", "items": [
    {"id": "T-100", "title": "曾纳入已归档 Sprint", "type": "技术", "points": 2,
     "priority": "Should", "status": "待办", "confirmed": True,
     "created_at": "2026-01-01", "planned_sprints": ["005"]},
    {"id": "T-101", "title": "从未纳入", "type": "功能", "points": 1,
     "priority": "Could", "status": "待办", "confirmed": True, "created_at": "2026-01-01"},
]}]}
(docs / "backlog.json").write_text(json.dumps(backlog, ensure_ascii=False), encoding="utf-8")
closed = live / "sprint-005-20260901.md"
closed.write_text("- 状态: 已关闭\n- 周期: 2026-W36\n\n## 任务清单\n- T-100 [2]\n", encoding="utf-8")
today = date(2026, 11, 2)

results = []
def case(name, ok):
    results.append(f"{name}={ok!s}")

case("scan_live", len(agile.scan_sprints(root)) == 1)
data = json.loads((docs / "backlog.json").read_text(encoding="utf-8"))
flags = {r["id"]: r["ever_planned"] for r in agile.collect_backlog_age(data, [], today)["aged"]}
case("stamp_union", flags["T-100"] is True and flags["T-101"] is False)
scanned = {r["id"]: r["ever_planned"] for r in
           agile.collect_backlog_age(data, agile.scan_sprints(root), today)["aged"]}
case("scan_covers_history", scanned["T-100"] is True and scanned["T-101"] is False)

calls = []
real = agile.collect_backlog_age
def counting(*args, **kwargs):
    calls.append(1)
    return real(*args, **kwargs)
agile.collect_backlog_age = counting
fp_before = agile.age_fingerprint(root)
agile.age_snapshot(root, today)
agile.age_snapshot(root, today)                        # 第二次命中缓存，不重算
shutil.move(str(closed), str(live / "archive" / closed.name))
snap = agile.age_snapshot(root, today)                 # 指纹变化 → 强制重算
lines = {line.split()[1]: line for line in snap["notice_items"]}
case("move_invalidates", len(calls) == 2 and agile.scan_sprints(root) == []
     and agile.age_fingerprint(root) != fp_before)
case("stamp_survives_archive", "曾纳入 Sprint" in lines["T-100"]
     and "从未纳入 Sprint" in lines["T-101"])

backlog["phases"][0]["items"][0]["planned_sprints"] = []   # 拿掉戳记：标签必然翻谎
(docs / "backlog.json").write_text(json.dumps(backlog, ensure_ascii=False), encoding="utf-8")
snap4 = agile.age_snapshot(root, today)
case("stamp_is_the_source", "从未纳入" in snap4["notice_items"][0] and len(calls) == 3)

state = " | ".join(agile.describe_state(root))
case("desc_no_sprint", "Sprint" not in state and "Backlog 2 条" in state)
(live / "sprint-005-20260901.done.yaml").write_text(
    "completed:\n- T-101\nmoved_next: []\n", encoding="utf-8")   # 迟到的回填
state2 = " | ".join(agile.describe_state(root))
case("late_backfill", agile.detect_stage(root) == "backfill"
     and "待回填 1 个" in state2 and "Sprint" not in state2)
agile.age_cache_path(root).unlink(missing_ok=True)     # 不在临时目录留探针残渣

print("\n".join(results))
print("ROOT=" + root.as_posix())
PY
)"
for line in $ARCH_OUT; do
  case "$line" in ROOT=*) continue ;; esac
  key="${line%%=*}"; val="${line#*=}"
  check "归档·$key" "True" "$val"
done
ARCH_ROOT="$(printf '%s\n' "$ARCH_OUT" | grep '^ROOT=' | cut -d= -f2-)"
check "归档后迟到回填仍判 backfill" "1" \
  "$(cd "$ARCH_ROOT" && "$PY" "$PLUGIN/scripts/agile.py" brief . 2>&1 | grep -c '^阶段：backfill')"
out=$(printf '{"tool_input":{"file_path":"%s/sprints/archive/sprint-005-20260901.md"}}' "$ARCH_ROOT" \
      | "$PY" "$PLUGIN/scripts/agile.py" hook-post-write)
check "写 archive 路径 hook 无输出" "" "$out"

printf '\nPASS=%d FAIL=%d\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
