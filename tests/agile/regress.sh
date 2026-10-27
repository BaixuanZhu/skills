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

# ⑤ CLI 冒烟：合规项目两个命令都要 exit 0
check "check  退出码" "0" "$(run check >/dev/null 2>&1; echo $?)"
check "stats  退出码" "0" "$(run stats >/dev/null 2>&1; echo $?)"

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

printf '\nPASS=%d FAIL=%d\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
