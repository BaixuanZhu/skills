#!/usr/bin/env python3
"""agile 套件的机械部分：Backlog 结构校验、统计、渲染、旧格式迁移、hook 入口。

为什么存在：点数和条目统计原先靠 agent 每次现场写脚本兑现，每次都不一样。
计算这件事不该交给模型。

设计取舍
--------
* **backlog.json 是唯一的 Backlog 文件。** 历史上的 PRODUCT-BACKLOG.md 渲染产物
  已随 5.6.0 退役（人读视图 = 问 agent 或 `agile.py stats`），为它维护的重渲染 /
  回滚 / 同步比对整套防漂移机制一并删除。脚本因此从不需要解析 Markdown，
  也不必写正则去容错列数漂移、全角空格、`\\|` 转义这些迟早会出问题的地方。
* **标准库 only，零正则。** 结构化数据用 json 模块，行级判断用 startswith / split。
* **hook stdout 只说 JSON。** CC 与 ZCode 都从 stdout 解析 hook 结果，但 ZCode 对
  不以 `{` 开头的输出**静默忽略**（= 永不注入），所以 hook 入口的 stdout 不许混任何
  日志或纯文本；要注入就走 `hookSpecificOutput.additionalContext`，要阻断就走顶层
  `decision: "block"` + `reason`（两家的交集形态）。
* **fail-open，且有意退出码只有 0。** 脚本随插件分发到别人机器上，任何未预期异常
  都变成沉默退出 0。hook 有意非零退出会破坏 hooks.json 里 `python || python3`
  的兜底语义（`||` 只该在解释器缺失时轮到第二个），所以问题清单走 stdout JSON。
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path

# ── 约定 ────────────────────────────────────────────────────────────────────
DOCS_DIR = "agile-docs"
BACKLOG_JSON = "backlog.json"
BACKLOG_MD = "PRODUCT-BACKLOG.md"
ADR_MD = "ADR.md"
STRATEGY_CONFLICT = "STRATEGY_CONFLICT.md"
SPRINT_DIRS = ("sprints", f"{DOCS_DIR}/sprints")

# 每轮提示文本的真源：脚本只判断阶段，文案在 markdown 里。
# 文案写进代码会让「改一句话」变成「改代码 + 记得同步两份副本」，且 review 时看不见。
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
BRIEF_REL = "skills/using-agile/references/turn-brief.md"

TYPES = ("技术", "功能")
PRIORITIES = ("Must", "Should", "Could", "Won't")
STATUSES = ("待办", "已完成", "已撤回")
FIB = (1, 2, 3, 5, 8, 13)
TODO_STATUS = "待办"
WITHDRAWN = "已撤回"
# Sprint 文件头只认这两个键、状态只认这两个词（见 using-agile/sprint-schema.yaml）。
# 收敛成常量是因为三处判定（解析白名单 / active 判定 / 状态行渲染）必须同步。
SPRINT_META_KEYS = ("状态", "周期")
SPRINT_STATUSES = ("规划完成", "已关闭")
SPRINT_CLOSED = "已关闭"
SPRINT_STATUS_UNKNOWN = "状态未识别"
# 三态 → 状态行显示词。unknown 显式显示，不照抄原值、更不静默当成进行中。
SPRINT_LABELS = {"closed": SPRINT_CLOSED, "planned": SPRINT_STATUSES[0], "unknown": SPRINT_STATUS_UNKNOWN}
ID_PREFIXES = ("T-", "F-")
QUOTES = "\"'“”‘’"
POINT_BRACKETS = (("(", ")"), ("（", "）"))
FEEDBACK_TYPES = ("reason", "issue", "decision")


# ── 输入输出（Windows 控制台默认 GBK，显式切 utf-8） ────────────────────────
def _init_io() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass


def read_stdin_json() -> dict:
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", "replace")
    except Exception:
        return {}
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def emit_context(event: str, text: str) -> None:
    """回注上下文（exit 0，模型看得到但不算错误）。

    顶层只放 hookSpecificOutput，additionalContext 挂在里面：ZCode 对本事件
    的 hookSpecificOutput 只认 additionalContext 这一个附加键，且 stdout 不以
    `{` 开头就直接忽略，所以这里前后都不能再打印纯文本。
    """
    payload = {"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")


def emit_block(reason: str) -> None:
    """阻断信号（exit 0）：CC 与 ZCode 都解析顶层 decision:block，reason 递给模型。

    不撤销已写入的内容（PostToolUse 时写盘已发生），只宣告这次写入不被认可并
    说明改哪里。不用 exit 2 + stderr：脚本有意退出码必须只有 0，否则 hooks.json
    的 `python || python3` 会在规范错误时重跑脚本、并用第二个解释器的缺失码
    掩盖信号。
    """
    payload = {"decision": "block", "reason": reason}
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")


# ── 数据层 ──────────────────────────────────────────────────────────────────
def load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def iter_items(data: dict):
    for phase in data.get("phases") or []:
        for item in phase.get("items") or []:
            yield phase, item


def is_item_id(value: str) -> bool:
    if not isinstance(value, str) or not value.startswith(ID_PREFIXES):
        return False
    tail = value[2:]
    return 3 <= len(tail) <= 4 and tail.isdigit()


def is_int(value) -> bool:
    """布尔是 int 的子类：`true` 会被 isinstance(..., int) 当成 1 混过整数校验。"""
    return isinstance(value, int) and not isinstance(value, bool)


def validate(data: dict) -> tuple[list[str], list[str]]:
    """返回 (errors, warnings)。errors 是结构性问题，warnings 是规范问题。"""
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(data.get("phases"), list):
        return ["缺少 phases 数组——顶层必须是 {\"schema\": 1, \"phases\": [{...}]}"], []

    seen: dict[str, str] = {}
    for index, phase in enumerate(data["phases"], start=1):
        if not isinstance(phase, dict):
            errors.append(f"phases[{index}] 不是对象")
            continue
        if not is_int(phase.get("id")):
            errors.append(f"phases[{index}] 缺少整数 id")
        if not phase.get("title"):
            errors.append(f"phases[{index}] 缺少 title")
        if not isinstance(phase.get("items"), list):
            errors.append(f"phases[{index}] 缺少 items 数组")
            continue
        phase_id = phase.get("id") if is_int(phase.get("id")) else index
        for item in phase["items"]:
            if not isinstance(item, dict):
                errors.append(f"阶段 {phase_id} 有非对象条目")
                continue
            ident = item.get("id")
            if not is_item_id(ident):
                errors.append(f"阶段 {phase_id} 条目 id「{ident}」不合规（T-/F- + 3~4 位数字）")
                continue
            if ident in seen:
                errors.append(f"{ident} 重复出现（阶段 {seen[ident]} 与阶段 {phase_id}）")
            seen[ident] = str(phase_id)

            for field in ("title", "type", "priority", "status"):
                if not item.get(field):
                    errors.append(f"{ident} 缺少必填字段 {field}")
            points = item.get("points")
            if not is_int(points) or points <= 0:
                errors.append(f"{ident} 的 points 必须是正整数，当前是 {points!r}")
            if not isinstance(item.get("confirmed"), bool):
                errors.append(f"{ident} 的 confirmed 必须是 true/false，当前是 {item.get('confirmed')!r}")

            if item.get("type") and item["type"] not in TYPES:
                warnings.append(f"{ident} 类型「{item['type']}」不在 {'/'.join(TYPES)}")
            if item.get("priority") and item["priority"] not in PRIORITIES:
                warnings.append(f"{ident} 优先级「{item['priority']}」不在 {'/'.join(PRIORITIES)}")
            if item.get("status") and item["status"] not in STATUSES:
                warnings.append(f"{ident} 状态「{item['status']}」不在 {'/'.join(STATUSES)}")
            if is_int(points) and points > 0 and points not in FIB:
                warnings.append(f"{ident} 点数 {points} 不在斐波那契 {'/'.join(map(str, FIB))}")
            detail = item.get("detail")
            if detail is not None and not isinstance(detail, list):
                warnings.append(f"{ident} 的 detail 必须是字符串数组")

    return errors, warnings


def compute_stats(data: dict) -> dict:
    """全量重算。已撤回的留痕不入账。"""
    live: list[tuple[int, dict]] = [
        (phase.get("id") if is_int(phase.get("id")) else 0, item)
        for phase, item in iter_items(data)
        if item.get("status") != WITHDRAWN
    ]
    total = len(live)
    points = sum(int(item.get("points") or 0) for item in (it for _, it in live))

    def group(key) -> list[tuple]:
        buckets: dict = {}
        for phase_id, item in live:
            k = key(phase_id, item)
            count, pts = buckets.get(k, (0, 0))
            buckets[k] = (count + 1, pts + int(item.get("points") or 0))
        return sorted(buckets.items(), key=lambda kv: kv[0])

    return {
        "total": total,
        "points": points,
        "confirmed": sum(1 for _, item in live if item.get("confirmed") is True),
        "withdrawn": sum(1 for _, item in iter_items(data) if item.get("status") == WITHDRAWN),
        "by_type": group(lambda _p, item: item.get("type") or "未标"),
        "by_phase": group(lambda phase_id, _item: phase_id),
        "by_priority": group(lambda _p, item: item.get("priority") or "未标"),
        "by_status": group(lambda _p, item: item.get("status") or "未标"),
    }


# ── 统计输出 ────────────────────────────────────────────────────────────────
def render_stats_lines(stats: dict) -> list[str]:
    def join(groups, with_points=True, prefix=""):
        parts = []
        for key, (count, points) in groups:
            label = f"{prefix}{key}"
            parts.append(f"{label} = {count} 条" + (f" / {points} 点" if with_points else ""))
        return "；".join(parts)

    lines = [f"- 条目：{stats['total']} 条 / {stats['points']} 点"]
    if stats["by_type"]:
        lines.append(f"- 按类型：{join(stats['by_type'])}")
    if stats["by_phase"]:
        lines.append(f"- 按阶段：{join(stats['by_phase'], prefix='阶段 ')}")
    if stats["by_priority"]:
        lines.append(f"- 按优先级：{join(stats['by_priority'])}")
    if stats["by_status"]:
        lines.append(f"- 按状态：{join(stats['by_status'], with_points=False)}")
    lines.append(f"- 已确认：{stats['confirmed']} 条 ✓ / {stats['total'] - stats['confirmed']} 条待确认")
    if stats["withdrawn"]:
        lines.append(f"- 已撤回：{stats['withdrawn']} 条（不计入以上统计）")
    return lines


# ── 跨文件读取（全部行扫描，不解析 Markdown 结构） ──────────────────────────
def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def root_of(backlog_path: Path) -> Path:
    """backlog.json 在 agile-docs/ 下时，项目根是上两层。"""
    parent = backlog_path.parent
    return parent.parent if parent.name == DOCS_DIR else parent


def unquote(value: str) -> str:
    return value.strip().strip(QUOTES)


def split_kv(line: str) -> tuple[str, str, str]:
    """拆 `键: 值`，半角与全角冒号都认。返回值里的 sep 为空表示这行不是键值行。

    取行内**最先出现**的冒号做分隔，两种冒号比位置、不比固定优先级。按固定优先级
    取全角会切坏「值内部带另一种冒号」的行：`状态: 已关闭（执行结果来源：…）`
    曾被切成键 `状态: 已关闭（执行结果来源`，不在白名单内整行丢弃，Sprint 状态
    随之丢失，已关闭 Sprint 全部被判 active。
    """
    positions = [(line.find(sep), sep) for sep in ("：", ":")]
    positions = [(idx, sep) for idx, sep in positions if idx != -1]
    if not positions:
        return line.strip(), "", ""
    idx, sep = min(positions)
    return line[:idx].strip().strip("*").strip(), sep, line[idx + 1 :].strip()


def parse_sprint_items(text: str) -> list[tuple[str, int | None]]:
    """sprint 任务清单：`- T-001 标题 (3) → ADR-007`。取 id 与括号里的点。

    全角括号也认——中文输入法下 `（3）` 太容易打出来，只认半角会让点数静默丢失。
    """
    found: list[tuple[str, int | None]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        parts = stripped[2:].strip().split(None, 1)
        if not parts or not is_item_id(parts[0]):
            continue
        # 允许 `- T-001` 这种只写 ID 的清单行：漏解析等于对账网少一个洞，
        # 而「写漏了标题」本身不该让存在性检查跟着失效。
        ident = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
        points = None
        for open_ch, close_ch in POINT_BRACKETS:
            close = rest.rfind(close_ch)
            if close == -1:
                continue
            opening = rest.rfind(open_ch, 0, close)
            if opening == -1:
                continue
            inner = rest[opening + 1: close].strip()
            if inner.isdigit():
                points = int(inner)
                break
        found.append((ident, points))
    return found


def parse_sprint_meta(text: str) -> dict[str, str]:
    """只取白名单键，避免把任务清单行也读成字段。

    三种写法都认：`- 状态: x`（模板）、`状态: x`（裸键值，早期手写与部分 fixture）、
    `**状态**: x`（加粗键）；分隔符半角全角都行；值带引号会剥掉（`"已关闭"` 不剥
    会被判成未关闭，阶段永远停在 active）。
    """
    meta: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        body = stripped[1:].strip() if stripped[0] in "-*" else stripped
        key, found, value = split_kv(body)
        if found and key in SPRINT_META_KEYS:
            meta.setdefault(key, unquote(value))
    return meta


def sprint_status(meta: dict[str, str]) -> str:
    """Sprint 状态归一成 `closed` / `planned` / `unknown`。

    「状态」只在这里解释一次：active 判定、状态行渲染、文件头校验都消费返回值，
    免得同一个概念在三处各写一遍判定、各自漂移。
    比对用前缀而不是整串：闭环注记会把状态行写成「已关闭（执行结果来源：…）」，
    整串相等会让已关闭 Sprint 永远 active（5.6.4 修的正是这个）。
    """
    status = meta.get("状态", "")
    if status.startswith(SPRINT_CLOSED):
        return "closed"
    if status.startswith(SPRINT_STATUSES[0]):
        return "planned"
    return "unknown"


def sprint_number(stem: str) -> str:
    """`sprint-<序号>-<日期>` 里的序号段，原样字符串（保留前导零：`071` 不是 `71`）。

    取不到返回空串。序号只在这里解析一次——排序与显示各解析一遍曾导致
    「排序按日期、显示按序号」，命名混用时 `[-1]` 取到的是旧 Sprint。
    """
    chunks = stem.split("-")
    return chunks[1] if len(chunks) > 1 and chunks[1].isdigit() else ""


def sprint_header_problems(name: str, meta: dict[str, str]) -> list[str]:
    """文件头状态行的可执行断言，`check` 与写后 hook 共用。

    解析层宽容（认三种写法、两种冒号），取值不放宽：状态词写岔时下游只会
    「静默当成进行中」，正是 5.6.4 那类故障的上游。
    """
    status = meta.get("状态", "")
    legal = "/".join(SPRINT_STATUSES)
    if not status:
        return [f"{name}: 缺状态行（合法值 {legal}）"]
    if sprint_status(meta) == "unknown":
        return [f"{name}: 状态「{status}」不在枚举 {legal} 内，当前按「进行中」处理"]
    return []


def parse_adr(text: str) -> tuple[int, int]:
    """ADR 总数与待拍板数。按条目括号切段再判断——数全文出现次数会把正文里的
    引用也算进去，得出「11 条 ADR 里 24 条 Proposed」。"""
    heads = ("## ADR-", "### ADR-")
    blocks: list[list[str]] = []
    current: list[str] | None = None
    for line in text.splitlines():
        if line.strip().startswith(heads):
            if current is not None:
                blocks.append(current)
            current = []
        elif current is not None:
            current.append(line)
    if current is not None:
        blocks.append(current)
    proposed = sum(1 for block in blocks if any("Proposed" in line for line in block))
    return len(blocks), proposed


def sprint_seq(stem: str) -> tuple[int, int, str]:
    """按序号排序，不按字符串——`sprint-10` 排到 `sprint-2` 前面，
    于是「当前 Sprint」取 `[-1]` 永远拿到 sprint-9，注入的状态是错的。"""
    number = sprint_number(stem)
    return (0, int(number), stem) if number else (1, 0, stem)


def scan_sprints(root: Path):
    """返回 [(文件路径, 文件主名, 元信息, 任务清单)]，按序号升序。

    每次调用读全部 Sprint 文件。两个 hook 每轮各调一次，Sprint 数到 50 上下
    才开始有可感知延迟——现在不值得加缓存，真到那一步再说。
    """
    found = []
    for rel in SPRINT_DIRS:
        directory = root / rel
        if not directory.is_dir():
            continue
        try:
            entries = sorted(directory.iterdir())
        except Exception:
            continue
        for path in entries:
            name = path.name
            if not name.startswith("sprint-") or not name.endswith(".md"):
                continue
            text = read_text(path)
            if text is None:
                continue
            found.append((path, path.stem, parse_sprint_meta(text), parse_sprint_items(text)))
    found.sort(key=lambda row: sprint_seq(row[1]))
    return found


def check_sprint_headers(root: Path) -> list[str]:
    """所有 Sprint 文件头的状态行必须是枚举词。

    `check` 里没有这条时，状态词写岔只会在下游表现成「阶段永远 active」，
    没人能顺着报错找到那一行——把契约从文档约定变成可执行断言。
    """
    return [
        line
        for _p, stem, meta, _items in scan_sprints(root)
        for line in sprint_header_problems(stem + ".md", meta)
    ]


def check_sprint_consistency(root: Path, data: dict) -> list[str]:
    """Backlog 与 Sprint 的点数/存在性对账。上一轮实测里 agent 自己发现了这类不同步。"""
    index = {}
    for _, item in iter_items(data):
        if item.get("id"):
            index[item["id"]] = item
    problems: list[str] = []
    for path, _stem, _meta, items in scan_sprints(root):
        for ident, points in items:
            item = index.get(ident)
            if item is None:
                problems.append(f"{path.name} 引用了 {ident}，但 backlog.json 里没有这个条目")
            elif points is not None and points != item.get("points"):
                problems.append(
                    f"{path.name} 写 {ident} = {points} 点，backlog.json 是 {item.get('points')} 点"
                )
    return problems


# ── 回填文件（.done.yaml）──────────────────────────────────────────────────────
def parse_done(text: str) -> dict:
    """只看回填文件固定的三层结构，不引通用 YAML 解析器。

    completed / moved_next 是 ID 列表（逐行 `- ID` 或内联 `[A, B]` 都认）；
    feedback 是 `- item / type / note` 的对象列表。块标量（`note: |`）不支持，
    note 是给人读的、脚本不校验其内容，多行会只取到 `|` 本身。
    """
    result: dict = {"completed": [], "moved_next": [], "feedback": []}
    section = ""
    current: dict | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        if indent == 0:
            head, found, tail = split_kv(line)
            current = None
            if not found or head not in result:
                section = ""
                continue
            section = head
            if tail.startswith("[") and tail.endswith("]"):
                for part in tail[1:-1].split(","):
                    value = unquote(part)
                    if value:
                        result[section].append(value)
            continue
        if section in ("completed", "moved_next"):
            if line[0] in "-*":
                value = unquote(line[1:])
                if value:
                    result[section].append(value)
        elif section == "feedback":
            if line[0] in "-*":
                current = {}
                result["feedback"].append(current)
                line = line[1:].strip()
                if not line:
                    continue
            if current is not None:
                head, found, tail = split_kv(line)
                if found:
                    current[head] = unquote(tail)
    return result


def inspect_done(path: Path, known: set[str]) -> list[str]:
    """单个回填文件的内容检查。known 是 backlog.json 里的合法条目 ID 集合。"""
    text = read_text(path)
    if text is None:
        return [f"{path.name} 读不出来（编码或权限）"]
    done = parse_done(text)
    problems: list[str] = []
    if not done["completed"] and not done["moved_next"]:
        problems.append(f"{path.name} 的 completed 与 moved_next 都空，回填至少要有一个非空数组")
    for key in ("completed", "moved_next"):
        seen = set()
        for ident in done[key]:
            if ident in seen:
                problems.append(f"{path.name} 的 {key} 里 {ident} 重复")
            seen.add(ident)
            if ident not in known:
                problems.append(f"{path.name} 的 {key} 引用 {ident}，backlog.json 里没有这个条目")
    for ident in sorted(set(done["completed"]) & set(done["moved_next"])):
        problems.append(f"{path.name} 的 {ident} 同时在 completed 与 moved_next（逻辑矛盾）")
    for entry in done["feedback"]:
        kind = entry.get("type", "")
        if kind and kind not in FEEDBACK_TYPES:
            problems.append(f"{path.name} 的 feedback type「{kind}」不在 {' / '.join(FEEDBACK_TYPES)} 内")
        ident = entry.get("item", "")
        if ident and ident not in known:
            problems.append(f"{path.name} 的 feedback 关联 {ident}，backlog.json 里没有这个条目")
    return problems


def check_done_files(root: Path, data: dict) -> list[str]:
    """回填文件的内容校验。

    文件名只能说明「有待闭环」，内容错了没人会发现——而闭环的下一步就是拿这份
    内容去同步 backlog。这里把「引用了不存在的条目」「同一 ID 既完成又顺延」
    「feedback 类型拼错」这类问题报出来。
    """
    known = {item["id"] for _phase, item in iter_items(data) if item.get("id")}
    problems: list[str] = []
    for rel in SPRINT_DIRS:
        directory = root / rel
        if not directory.is_dir():
            continue
        try:
            files = sorted(p for p in directory.iterdir() if p.name.endswith(".done.yaml"))
        except Exception:
            continue
        for path in files:
            problems.extend(inspect_done(path, known))
    return problems



# ── hook 入口 ───────────────────────────────────────────────────────────────
def payload_root(payload: dict) -> Path:
    raw = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        return Path(raw)
    except Exception:
        return Path.cwd()


def hook_post_write() -> None:
    payload = read_stdin_json()
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    raw = tool_input.get("file_path") or tool_input.get("filePath") or tool_input.get("path") or ""
    raw = str(raw)
    if not raw:
        return
    root = payload_root(payload)
    path = Path(raw) if os.path.isabs(raw) else root / raw

    if path.name == BACKLOG_JSON:
        handle_json_write(path)
    elif path.name.endswith(".done.yaml"):
        handle_done_write(path, root)
    elif path.suffix == ".md" and path.name.startswith("sprint-") and path.parent.name == "sprints":
        # 只认 sprints/ 下的 sprint-*.md：项目根放一份 sprint-notes.md 不该被当成
        # Sprint 文件质问，这也是 scan_sprints 的扫描范围。
        handle_sprint_write(path)


def handle_json_write(json_path: Path) -> None:
    text = read_text(json_path)
    if text is None:
        return
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        emit_block(
            "[agile] backlog.json 不是合法 JSON，本文件必须机器可读。\n"
            f"  第 {exc.lineno} 行第 {exc.colno} 列：{exc.msg}\n"
            "  常见原因：写了注释、结尾多了逗号、用了中文引号、字符串里没转义换行。"
        )
        return

    errors, warnings = validate(data)
    if errors:
        listed = "\n".join("  · " + line for line in errors)
        emit_block(
            f"[agile] backlog.json 结构不合规（{len(errors)} 处）：\n{listed}\n"
            "  字段说明见 agile-backlog/references/backlog-rules.md §七。"
            "改对之后会自动重新渲染 Markdown。"
        )
        return

    notes = list(warnings)
    notes.extend(check_sprint_consistency(root_of(json_path), data))
    if notes:
        listed = "\n".join("  · " + line for line in notes)
        emit_context(
            "PostToolUse",
            f"[agile] backlog.json 已通过结构校验，另有 {len(notes)} 处待处理：\n{listed}",
        )


def handle_done_write(done_path: Path, root: Path) -> None:
    """回填写完立刻校验内容。

    用 additionalContext 提示而不是 decision:block：回填允许分次写，中途
    半成品不应该被打断。真正强制在 `check` 与关闭 Sprint 之前——那时内容
    必须已经定型。
    """
    json_path = root / DOCS_DIR / BACKLOG_JSON
    if not json_path.exists():
        return
    data = load_json(json_path)
    if data is None:
        return
    known = {item["id"] for _phase, item in iter_items(data) if item.get("id")}
    problems = inspect_done(done_path, known)
    if not problems:
        return
    listed = "\n".join("  · " + line for line in problems)
    emit_context(
        "PostToolUse",
        f"[agile] 回填文件 {done_path.name} 有 {len(problems)} 处问题：\n{listed}\n"
        "  口径见 agile-docs/interfaces/sprint-schema.yaml 的 done_file 段。",
    )


def handle_sprint_write(sprint_path: Path) -> None:
    """Sprint 文件头写完立刻校验状态行。

    用 additionalContext 而不是 decision:block：规划 Sprint 允许分次写，
    中途还没写到文件头不该被打断。强制在 `check` 与关闭 Sprint 之前。
    只查状态行——其余段落齐不齐由闭环检查清单负责，脚本不越位。
    """
    text = read_text(sprint_path)
    if text is None:
        return
    problems = sprint_header_problems(sprint_path.name, parse_sprint_meta(text))
    if not problems:
        return
    listed = "\n".join("  · " + line for line in problems)
    emit_context(
        "PostToolUse",
        f"[agile] Sprint 文件头状态行有问题：\n{listed}\n"
        "  合法值：规划完成 / 已关闭（状态词后可跟全角括号备注），见 sprint-schema.yaml 的 sprint_file.status。",
    )


def pending_backfills(root: Path) -> list[str]:
    """未闭环的回填文件名（`sprints/*.done.yaml`）。"""
    pending: list[str] = []
    for rel in SPRINT_DIRS:
        directory = root / rel
        if not directory.is_dir():
            continue
        try:
            pending.extend(p.name[: -len(".done.yaml")] for p in directory.iterdir() if p.name.endswith(".done.yaml"))
        except Exception:
            continue
    return pending


def active_sprints(root: Path) -> list[tuple[str, dict]]:
    """状态不是「已关闭」的 Sprint，包括状态缺失或写岔（unknown）的。

    未知状态按 active 计是保守方向：把可能还开着的 Sprint 判成关闭，
    会让待办条目被重复规划一遍。unknown 的显式暴露交给 describe_state
    与 check，不靠这里静默降级。
    """
    return [
        (stem, meta)
        for _p, stem, meta, _items in scan_sprints(root)
        if sprint_status(meta) != "closed"
    ]


def detect_stage(root: Path) -> str:
    """当前处在流程的哪一步。顺序即优先级。

    判据看重「最靠后的里程碑」，不是严格按层顺序：套件允许用户显式跳层
    （agile-backlog §0），已有条目的项目不能被判回「战略层未起步」；
    进行中的 Sprint 也比建池靠后，池耗尽仍判 active。
    sprint 只认「待办」活条目（agile-sprint §0 的取条前置）——条目全部
    完成/撤回的池子撑不起 Sprint，落回 backlog 段提示补池。
    与 turn-brief.md 的阶段表一一对应；改这里要同步改那张表。
    """
    docs = root / DOCS_DIR
    if not docs.is_dir():
        return ""
    if (docs / STRATEGY_CONFLICT).exists():
        return "conflict"
    if pending_backfills(root):
        return "backfill"

    has_vision = (docs / "VISION.md").exists()
    has_arch = (docs / "ARCHITECTURE.md").exists()
    has_adr = (docs / ADR_MD).exists()
    json_path = docs / BACKLOG_JSON
    data = load_json(json_path) if json_path.exists() else None
    has_todo = data is not None and any(
        item.get("status") == TODO_STATUS for _phase, item in iter_items(data)
    )

    if active_sprints(root):
        return "active"
    if has_todo:
        return "sprint"
    if not has_vision:
        return "init"
    if not (has_arch and has_adr):
        return "architecture"
    return "backlog"


def parse_briefs(text: str) -> dict[str, str]:
    """解析 `[agile-brief:阶段]` 块。用 startswith 行扫描，不用正则。"""
    briefs: dict[str, str] = {}
    current: str | None = None
    buffer: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("[agile-brief:") and line.endswith("]"):
            current = line[len("[agile-brief:") : -1].strip()
            buffer = []
        elif line.startswith("[/agile-brief:"):
            if current:
                body = "\n".join(buffer).strip()
                if body:
                    briefs[current] = body
            current = None
            buffer = []
        elif current is not None:
            buffer.append(raw.rstrip())
    return briefs


def load_briefs() -> dict[str, str]:
    text = read_text(PLUGIN_ROOT / BRIEF_REL)
    return parse_briefs(text) if text else {}


def build_state_block(root: Path) -> str:
    """每轮 / 每次会话注入的 `<agile-state>` 块：状态快照 + 本阶段该做什么。"""
    parts = describe_state(root)
    body = "｜".join(parts) if parts else "agile-docs/ 已存在"
    stage = detect_stage(root)
    brief = load_briefs().get(stage, "") if stage else ""
    if not brief:
        # 故意显眼：文案文件缺失或被改名时，要让模型知道自己在裸奔，而不是静默降级。
        brief = f"阶段说明缺失（{BRIEF_REL} 里没有 [{stage or '?'}] 块），按 `using-agile` 自行判断该走哪一步。"
    return "\n".join(["<agile-state>", body, brief, ROUTING_LINE, "</agile-state>"])


def describe_state(root: Path) -> list[str]:
    """Sprint / 回填 / Backlog / ADR 的一行式摘要，两个 hook 共用。"""
    docs = root / DOCS_DIR
    json_path = docs / BACKLOG_JSON
    parts: list[str] = []

    sprints = scan_sprints(root)
    if sprints:
        _path, stem, meta, _items = sprints[-1]
        seq = sprint_number(stem) or stem
        # 状态只显示状态词：闭环注记「（执行结果来源：…）」不进这行（每轮都注入，
        # 不能随备注长度膨胀）。写岔的状态显示成「状态未识别」而不是照抄原文——
        # 静默降级成进行中，正是这类故障活了 9 个 Sprint 的原因。
        bits = [f"Sprint {seq}", SPRINT_LABELS[sprint_status(meta)]]
        if meta.get("周期"):
            bits.append("(" + meta["周期"] + ")")
        parts.append(" ".join(bits))

    pending = pending_backfills(root)
    if pending:
        # 只报数量 + 至多 3 个名字：这一行每轮都进上下文，不能随项目规模线性膨胀。
        names = sorted(pending)
        shown = "、".join(names[:3]) + (" 等" if len(names) > 3 else "")
        parts.append(f"待回填 {len(pending)} 个（{shown}）")

    data = load_json(json_path) if json_path.exists() else None
    if data is not None:
        stats = compute_stats(data)
        parts.append(f"Backlog {stats['total']} 条 / {stats['points']} 点（已确认 {stats['confirmed']}）")

    adr_text = read_text(docs / ADR_MD)
    if adr_text:
        total, proposed = parse_adr(adr_text)
        if total:
            parts.append(f"ADR {total} 条（{proposed} 条 Proposed 待拍板）" if proposed else f"ADR {total} 条")

    return parts


def hook_session() -> None:
    payload = read_stdin_json()
    root = payload_root(payload)
    if not (root / DOCS_DIR).is_dir():
        return  # 项目没启用敏捷套件 → 完全沉默
    emit_context("SessionStart", build_state_block(root))


# ── 本轮 triage（UserPromptSubmit） ─────────────────────────────────────────
SKIP_KEYWORD = "no-agile"

# 只为「建立或改动规划」提示；写代码、修 bug、查日志不该被念。
PLANNING_SIGNALS = (
    "规划", "路线图", "roadmap", "backlog", "sprint", "迭代", "待办",
    "用户故事", "优先级", "拆解", "里程碑", "mvp", "敏捷", "adr",
)

ROUTING_LINE = "纯执行任务（写码 / 修 bug / 查日志）直接做；动规划先读上面点到的那个技能。"


def hint_marker(root: Path, session: str) -> Path:
    """同一会话只提示一次的新项目提示位；无 session_id 时退化为「同项目同一天一次」。"""
    key = session or (str(root) + time.strftime("%Y-%m-%d"))
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"agile-hint-{digest}.marker"


def hook_prompt() -> None:
    payload = read_stdin_json()
    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        return
    lowered = prompt.lower()
    if SKIP_KEYWORD in lowered:
        return  # 用户本轮明确不要敏捷

    root = payload_root(payload)
    if (root / DOCS_DIR).is_dir():
        # 长会话被 compact 后 SessionStart 的内容会丢，这里每轮补：状态 + 本阶段该做什么。
        # 只要 agile-docs/ 存在就注入，哪怕 backlog.json 还没建——战略层做到一半才最需要。
        emit_context("UserPromptSubmit", build_state_block(root))
        return

    hits = [word for word in PLANNING_SIGNALS if word in lowered]
    if not hits:
        return
    marker = hint_marker(root, str(payload.get("session_id") or ""))
    if marker.exists():
        return
    try:
        marker.write_text("1", encoding="utf-8")
    except Exception:
        return
    emit_context(
        "UserPromptSubmit",
        "<agile-hint>\n"
        f"这轮命中「{'/'.join(hits)}」。命中规划词 ≠ 要建套件：小体量（单需求、一次性拆解、"
        "小改动）直接答，不提本套件；体量到了（单轮 ≥3 个需求点，或多轮迭代/排期/里程碑，"
        "或存量项目要长期规划）只推荐一次「要不要初始化敏捷套件」、等用户拍板；明示要建才读 "
        "`using-agile` §4 走初始化（先问项目画像，不写任何文件）。\n"
        "</agile-hint>",
    )


# ── 命令行 ──────────────────────────────────────────────────────────────────
USAGE = """agile.py —— Backlog 机械操作（标准库 only，零正则）

  stats   [项目根]   打印统计（每次全量重算，已撤回不计入；backlog.json 是唯一 Backlog 文件）
  check   [项目根]   结构校验 + Sprint 点数对账 + 回填内容，有问题返回 1
  brief   [项目根]   打印当前阶段与每轮将要注入的内容（排查 hook 用）

  hook-post-write    hook 入口：写完文件后校验（decision:block = 需要模型处理）
  hook-session       hook 入口：会话开始注入敏捷状态
  hook-prompt        hook 入口：每轮判断本轮要不要走敏捷流程
"""


def resolve(root_arg: str | None) -> tuple[Path, Path, Path]:
    root = Path(root_arg) if root_arg else Path.cwd()
    docs = root / DOCS_DIR
    return root, docs / BACKLOG_JSON, docs / BACKLOG_MD


def read_backlog(json_path: Path) -> tuple[dict | None, str]:
    """读 backlog.json，返回 (数据, 问题描述)。问题为空串表示读到了。"""
    if not json_path.exists():
        return None, f"找不到 {json_path}"
    data = load_json(json_path)
    return (data, "") if data is not None else (None, f"{json_path} 不是合法 JSON")


def cli_stats(root_arg: str | None) -> int:
    _root, json_path, _md_path = resolve(root_arg)
    data, problem = read_backlog(json_path)
    if data is None:
        print(problem)
        print("  旧表格格式：由 agent 按 agile-backlog/references/backlog-rules.md §七 一次性转写")
        return 1
    print("\n".join(render_stats_lines(compute_stats(data))))
    return 0


def cli_check(root_arg: str | None) -> int:
    root, json_path, md_path = resolve(root_arg)
    # Sprint 头单独先查：它和 backlog.json 无关，backlog 缺失或写坏时这条
    # 照样要报出来——状态词写岔正是「阶段判错」的上游，不该被另一个文件的
    # 错误挡住。
    problems: list[str] = ["Sprint 头：" + line for line in check_sprint_headers(root)]

    data, problem = read_backlog(json_path)
    if data is None:
        problems.append("结构：" + problem)
    else:
        errors, warnings = validate(data)
        problems.extend("结构：" + line for line in errors)
        problems.extend("规范：" + line for line in warnings)
        problems.extend("跨文件：" + line for line in check_sprint_consistency(root, data))
        problems.extend("回填：" + line for line in check_done_files(root, data))

    if md_path.exists():
        # PRODUCT-BACKLOG.md 已随 5.6.0 退役：不再生成、不再比对，只提醒清理。
        print(f"提示：{md_path.name} 已不再生成（遗留产物，确认无自定义内容后可删除）")

    if not problems:
        stats = compute_stats(data)
        print(f"通过：{stats['total']} 条 / {stats['points']} 点，结构 / 对账 / 回填 / Sprint 头全过")
        return 0
    print(f"发现 {len(problems)} 处问题：")
    for line in problems:
        print("  · " + line)
    return 1


def cli_brief(root_arg: str | None) -> int:
    """打印当前阶段与将要注入的内容——排查「hook 为什么没说话」时用这个。"""
    root = Path(root_arg) if root_arg else Path.cwd()
    if not (root / DOCS_DIR).is_dir():
        print("没有 agile-docs/：视为新项目，只在提问命中规划类词时提示一次入口（同会话一次）")
        return 0
    stage = detect_stage(root)
    brief = load_briefs().get(stage, "")
    print(f"阶段：{stage or '（未识别）'}")
    if not brief:
        print(f"⚠ {BRIEF_REL} 里没有 [{stage}] 块，注入会退化为「阶段说明缺失」")
    print()
    print(build_state_block(root))
    return 0


COMMANDS = {
    "stats": cli_stats,
    "check": cli_check,
    "brief": cli_brief,
}


def log_hook_error() -> None:
    """把当前异常追加到临时日志。只在 AGILE_DEBUG 非空时动手。

    靠环境变量开关而不是配置文件：排查是一次性的，不需要一份要维护的设置。
    写日志本身再出错也吞掉——这条路径上任何非零退出都会破坏 hooks.json 的
    `python || python3` 兜底。
    """
    if not os.environ.get("AGILE_DEBUG"):
        return
    try:
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with (Path(tempfile.gettempdir()) / "agile-hook.log").open("a", encoding="utf-8") as fh:
            fh.write(f"--- {stamp} {sys.argv[1] if len(sys.argv) > 1 else ''}\n")
            traceback.print_exc(file=fh)
    except BaseException:
        pass


def main(argv: list[str]) -> int:
    _init_io()
    command = argv[1] if len(argv) > 1 else "help"
    if command in ("help", "-h", "--help"):
        print(USAGE)
        return 0
    if command == "hook-post-write":
        hook_post_write()
        return 0
    if command == "hook-session":
        hook_session()
        return 0
    if command == "hook-prompt":
        hook_prompt()
        return 0
    handler = COMMANDS.get(command)
    if handler is None:
        print(USAGE)
        return 1
    root_arg = argv[2] if len(argv) > 2 and not argv[2].startswith("-") else None
    return handler(root_arg)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "help"
    if mode.startswith("hook-"):
        # fail-open：门禁脚本自己出错时沉默退出，不能让每次编辑都弹一条错误。
        # hook 的有意退出码只有 0（问题清单走 stdout JSON），所以任何异常——
        # 包括 SystemExit——都吞掉换 0：hooks.json 的 `python || python3` 兜底
        # 因此只在解释器缺失（127/9009）时才轮到第二个，不会重跑脚本或掩盖信号。
        try:
            main(sys.argv)
        except BaseException:
            # 静默是设计（见模块 docstring），但完全不可观测会让这类故障查不动：
            # AGILE_DEBUG 非空时把 traceback 落到临时日志，平时仍然一声不响。
            log_hook_error()
        sys.exit(0)
    sys.exit(main(sys.argv))
