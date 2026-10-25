#!/bin/sh
# agile.py 代码质量回归：每一条都对应一个曾经真实出错的点。
# 用法：sh plugins/agile/tests/regress.sh（解释器叫 python3 的环境：PY=python3 sh …）
#
# 注意：所有 python 片段都用相对路径 + 先 cd 进目标目录。Git Bash 里
# `/i/...`、`/tmp/...` 这类 POSIX 路径写在 `-c` 程序内部不会被翻译，
# Windows 解释器找不到（这正是本脚本第一版自己踩的坑）。
set -u
PLUGIN="$(cd "$(dirname "$0")/.." && pwd)"
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
printf -- '- **状态**: 进行中\n- **周期**: 2026-W99\n' > "$WORK/agile-docs/sprints/sprint-12.md"
BRIEF="$(run brief)"
check "两位数序号取到最后一个 Sprint" "1" "$(printf '%s' "$BRIEF" | grep -c 'Sprint 12 进行中')"
check "不会被 sprint-9 顶替" "0" "$(printf '%s' "$BRIEF" | grep -c 'Sprint 9 ')"

# ② 遗留 md 里的转义竖线：按裸 | 切会让整行左移一位
cat > "$WORK/agile-docs/PRODUCT-BACKLOG.md" <<'MD'
## 阶段 1 · 基础
| ID | 标题 | 类型 | 仓库 | 点 | 优先级 | 状态 | 关联 | 来源/依据 | 已确认 |
|----|------|------|------|---|--------|------|------|-----------|--------|
| T-001 | 支持 A \| B 双写 | 技术 | — | 3 | Must | 待办 | — | 需求 | ✓ |
MD
run migrate >/dev/null 2>&1
check "迁移保留标题里的竖线" "支持 A | B 双写|3|Must|True" \
  "$(cd "$WORK" && "$PY" -c "
import json
i=json.load(open('agile-docs/backlog.json',encoding='utf-8'))['phases'][0]['items'][0]
print('|'.join(map(str,[i['title'],i['points'],i['priority'],i['confirmed']])))")"

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

# ⑤ CLI 冒烟：合规项目上三个命令都要 exit 0
check "render 退出码" "0" "$(run render >/dev/null 2>&1; echo $?)"
check "check  退出码" "0" "$(run check >/dev/null 2>&1; echo $?)"
check "stats  退出码" "0" "$(run stats >/dev/null 2>&1; echo $?)"

# ⑥ 非法结构必须 exit 1，不能静默通过
(cd "$WORK" && "$PY" -c "
import json
p='agile-docs/backlog.json'; d=json.load(open(p,encoding='utf-8'))
d['phases'][0]['items'][0]['points']=0
json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False)")
check "points=0 被判错" "1" "$(run check >/dev/null 2>&1; echo $?)"

# ⑦ md 被手改后必须能和 json 对不上
printf '\n手工追加\n' >> "$WORK/agile-docs/PRODUCT-BACKLOG.md"
check "手改 md 被判不同步" "1" "$(run check >/dev/null 2>&1; echo $?)"

# ⑧ 布尔是 int 的子类：`"points": true` 不能被当成 1 点放行
(cd "$WORK" && "$PY" -c "
import json
p='agile-docs/backlog.json'; d=json.load(open(p,encoding='utf-8'))
d['phases'][0]['items'][0]['points']=True
json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False)")
check "points=true 被判错" "1" "$(run check >/dev/null 2>&1; echo $?)"
check "报的是点数不是斐波那契" "1" "$(run check 2>&1 | grep -c 'points 必须是正整数')"

# ⑨ md 缺失时提示必须说「缺失」，不能说「不一致」
rm -f "$WORK/agile-docs/PRODUCT-BACKLOG.md"
check "md 缺失报缺失" "1" "$(run check 2>&1 | grep -c '缺失或读不出来')"

printf '\nPASS=%d FAIL=%d\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
