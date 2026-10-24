#!/usr/bin/env python3
"""agile 套件的机械部分：Backlog 结构校验、统计、渲染、旧格式迁移、hook 入口。

为什么存在：点数和条目统计原先靠 agent 每次现场写脚本兑现，每次都不一样。
计算这件事不该交给模型。

设计取舍
--------
* **JSON 是真源，Markdown 是渲染产物。** 脚本从不需要解析 Markdown 表格，
  因此也不必写正则去容错列数漂移、全角空格、`\\|` 转义这些迟早会出问题的地方。
* **标准库 only，零正则。** 结构化数据用 json 模块，行级判断用 startswith / split。
* **fail-open。** 脚本随插件分发到别人机器上，任何未预期异常都变成沉默退出 0。
  门禁自己挂掉，不能连带把用户的工作流挂掉。
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

# ── 约定 ────────────────────────────────────────────────────────────────────
SCHEMA = 1
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
WITHDRAWN = "已撤回"
CONFIRMED_MARK = "✓"
EMPTY_MARK = "—"
ID_PREFIXES = ("T-", "F-")
HASH_KEY = "backlog-sha256"
RENDER_NOTICE = (
    "> 本文件由 `agile.py render` 从 `backlog.json` 生成，**改条目请改 `backlog.json`**。\n"
    "> 直接编辑本文件的内容会在下次写入时被渲染覆盖。"
)


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
    """以 hook 协议回注上下文（exit 0，模型看得到但不算错误）。"""
    payload = {"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")


def fail(message: str) -> None:
    """exit 2：PostToolUse 下把 stderr 递给模型，不撤销已写入的内容。"""
    sys.stderr.write(message.rstrip() + "\n")
    sys.exit(2)


# ── 数据层 ──────────────────────────────────────────────────────────────────
def load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def dump_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def fingerprint(data: dict) -> str:
    """与格式无关的数据指纹：键序无关、空白无关，只反映内容。"""
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def iter_items(data: dict):
    for phase in data.get("phases") or []:
        for item in phase.get("items") or []:
            yield phase, item


def is_item_id(value: str) -> bool:
    if not isinstance(value, str) or not value.startswith(ID_PREFIXES):
        return False
    tail = value[2:]
    return 3 <= len(tail) <= 4 and tail.isdigit()


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
        if not isinstance(phase.get("id"), int):
            errors.append(f"phases[{index}] 缺少整数 id")
        if not phase.get("title"):
            errors.append(f"phases[{index}] 缺少 title")
        if not isinstance(phase.get("items"), list):
            errors.append(f"phases[{index}] 缺少 items 数组")
            continue
        phase_id = phase.get("id") if isinstance(phase.get("id"), int) else index
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
            if not isinstance(points, int) or points <= 0:
                errors.append(f"{ident} 的 points 必须是正整数，当前是 {points!r}")
            if not isinstance(item.get("confirmed"), bool):
                errors.append(f"{ident} 的 confirmed 必须是 true/false，当前是 {item.get('confirmed')!r}")

            if item.get("type") and item["type"] not in TYPES:
                warnings.append(f"{ident} 类型「{item['type']}」不在 {'/'.join(TYPES)}")
            if item.get("priority") and item["priority"] not in PRIORITIES:
                warnings.append(f"{ident} 优先级「{item['priority']}」不在 {'/'.join(PRIORITIES)}")
            if item.get("status") and item["status"] not in STATUSES:
                warnings.append(f"{ident} 状态「{item['status']}」不在 {'/'.join(STATUSES)}")
            if isinstance(points, int) and points > 0 and points not in FIB:
                warnings.append(f"{ident} 点数 {points} 不在斐波那契 {'/'.join(map(str, FIB))}")
            detail = item.get("detail")
            if detail is not None and not isinstance(detail, list):
                warnings.append(f"{ident} 的 detail 必须是字符串数组")

    return errors, warnings


def compute_stats(data: dict) -> dict:
    """全量重算。已撤回的留痕不入账。"""
    live: list[tuple[int, dict]] = [
        (phase.get("id") if isinstance(phase.get("id"), int) else 0, item)
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


# ── 渲染层 ──────────────────────────────────────────────────────────────────
def cell(value) -> str:
    """表格单元格：竖线转义，空值统一占位符。"""
    if value is None or value == "":
        return EMPTY_MARK
    return str(value).replace("|", "\\|").replace("\n", " ")


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


def render_md(data: dict) -> str:
    """把 backlog.json 渲染成给人看的 Markdown。脚本本身从不反向解析它。"""
    out: list[str] = ["# 产品待办", "", RENDER_NOTICE, "", f"<!-- {HASH_KEY}: {fingerprint(data)} -->", ""]

    for phase in data.get("phases") or []:
        out.append(f"## 阶段 {phase.get('id', '?')} · {phase.get('title', '')}")
        out.append("")
        out.append("| ID | 标题 | 类型 | 仓库 | 点 | 优先级 | 状态 | 关联 | 来源/依据 | 已确认 |")
        out.append("|----|------|------|------|---|--------|------|------|-----------|--------|")
        for item in phase.get("items") or []:
            row = [
                cell(item.get("id")),
                cell(item.get("title")),
                cell(item.get("type")),
                cell(item.get("repo")),
                cell(item.get("points")),
                cell(item.get("priority")),
                cell(item.get("status")),
                cell(item.get("refs")),
                cell(item.get("basis")),
                CONFIRMED_MARK if item.get("confirmed") is True else "待确认",
            ]
            out.append("| " + " | ".join(row) + " |")
        out.append("")

    detailed = [item for _, item in iter_items(data) if item.get("detail")]
    if detailed:
        out.append("## 任务详情")
        out.append("")
        for item in detailed:
            out.append(f"### {item.get('id')} {item.get('title', '')}")
            out.append("")
            for line in item["detail"]:
                out.append(f"- {line}")
            out.append("")

    out.append("## 统计")
    out.append("")
    out.extend(render_stats_lines(compute_stats(data)))
    return "\n".join(out) + "\n"


def read_embedded_fingerprint(text: str) -> str | None:
    """取渲染时写下的指纹。行扫描，不解析表格。"""
    marker = f"<!-- {HASH_KEY}:"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(marker) and stripped.endswith("-->"):
            return stripped[len(marker): -3].strip()
    return None


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


def parse_sprint_items(text: str) -> list[tuple[str, int | None]]:
    """sprint 任务清单：`- T-001 标题 (3) → ADR-007`。取 id 与括号里的点。"""
    found: list[tuple[str, int | None]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        parts = stripped[2:].strip().split(None, 1)
        if len(parts) != 2 or not is_item_id(parts[0]):
            continue
        ident, rest = parts
        points = None
        close = rest.rfind(")")
        if close != -1:
            opening = rest.rfind("(", 0, close)
            if opening != -1:
                inner = rest[opening + 1: close].strip()
                if inner.isdigit():
                    points = int(inner)
        found.append((ident, points))
    return found


def parse_sprint_meta(text: str) -> dict[str, str]:
    """只取白名单键，避免把任务清单行也读成字段。"""
    wanted = ("状态", "周期", "目标")
    meta: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        body = stripped[2:].strip()
        for sep in ("：", ":"):
            if sep in body:
                key, _, value = body.partition(sep)
                key = key.strip()
                if key in wanted:
                    meta.setdefault(key, value.strip())
                break
    return meta


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


def scan_sprints(root: Path):
    """返回 [(文件路径, 文件主名, 元信息, 任务清单)]，按序号升序。"""
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
    found.sort(key=lambda row: row[1])
    return found


def check_sprint_consistency(root: Path, data: dict) -> list[str]:
    """Backlog 与 Sprint 的点数/存在性对账。上一轮实测里 agent 自己发现了这类不同步。"""
    index = {}
    for _, item in iter_items(data):
        if item.get("id"):
            index[item["id"]] = item
    problems: list[str] = []
    for path, stem, _meta, items in scan_sprints(root):
        for ident, points in items:
            item = index.get(ident)
            if item is None:
                problems.append(f"{path.name} 引用了 {ident}，但 backlog.json 里没有这个条目")
            elif points is not None and points != item.get("points"):
                problems.append(
                    f"{path.name} 写 {ident} = {points} 点，backlog.json 是 {item.get('points')} 点"
                )
    return problems


# ── 旧格式迁移（唯一需要读 Markdown 表格的地方，一次性） ─────────────────────
def convert_legacy_md(text: str) -> dict:
    phases: list[dict] = []
    details: dict[str, list[str]] = {}
    phase: dict | None = None
    in_detail = False
    detail_id: str | None = None

    def clean(value: str) -> str:
        return "" if value in ("—", "-", "无", "") else value

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            if heading.startswith("阶段"):
                body = heading[2:].strip()
                number, _, name = body.partition("·")
                number = number.strip()
                phase = {
                    "id": int(number) if number.isdigit() else len(phases) + 1,
                    "title": name.strip() or "未命名",
                    "items": [],
                }
                phases.append(phase)
                in_detail = False
                detail_id = None
            elif heading.startswith("任务详情"):
                phase, in_detail, detail_id = None, True, None
            else:
                phase, in_detail, detail_id = None, False, None
            continue

        if in_detail:
            if stripped.startswith("### "):
                parts = stripped[4:].strip().split(None, 1)
                detail_id = parts[0] if parts and is_item_id(parts[0]) else None
                if detail_id:
                    details.setdefault(detail_id, [])
            elif detail_id and stripped.startswith("- "):
                details[detail_id].append(stripped[2:].strip())
            continue

        if phase is None or not stripped.startswith("|"):
            continue
        cells = [part.strip() for part in stripped.strip("|").split("|")]
        if len(cells) < 10 or not is_item_id(cells[0]):
            continue
        points = int(cells[4]) if cells[4].isdigit() else 0
        item = {
            "id": cells[0],
            "title": cells[1],
            "type": cells[2],
            "repo": clean(cells[3]),
            "points": points,
            "priority": cells[5],
            "status": cells[6],
            "refs": clean(cells[7]),
            "basis": clean(cells[8]),
            "confirmed": cells[9] == CONFIRMED_MARK,
        }
        phase["items"].append(item)

    for phase in phases:
        for item in phase["items"]:
            if details.get(item["id"]):
                item["detail"] = details[item["id"]]
    return {"schema": SCHEMA, "phases": phases}


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
    elif path.name == BACKLOG_MD:
        handle_md_write(path)


def handle_json_write(json_path: Path) -> None:
    text = read_text(json_path)
    if text is None:
        return
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        fail(
            "[agile] backlog.json 不是合法 JSON，本文件必须机器可读。\n"
            f"  第 {exc.lineno} 行第 {exc.colno} 列：{exc.msg}\n"
            "  常见原因：写了注释、结尾多了逗号、用了中文引号、字符串里没转义换行。"
        )
        return

    errors, warnings = validate(data)
    if errors:
        listed = "\n".join("  · " + line for line in errors)
        fail(
            f"[agile] backlog.json 结构不合规（{len(errors)} 处）：\n{listed}\n"
            "  字段说明见 agile-backlog/references/backlog-rules.md §七。"
            "改对之后会自动重新渲染 Markdown。"
        )
        return

    md_path = json_path.with_name(BACKLOG_MD)
    try:
        md_path.write_text(render_md(data), encoding="utf-8")
    except Exception:
        return

    notes = list(warnings)
    notes.extend(check_sprint_consistency(root_of(json_path), data))
    if notes:
        listed = "\n".join("  · " + line for line in notes)
        emit_context(
            "PostToolUse",
            f"[agile] backlog.json 已通过结构校验并重新渲染 {BACKLOG_MD}，另有 {len(notes)} 处待处理：\n{listed}",
        )


def handle_md_write(md_path: Path) -> None:
    json_path = md_path.with_name(BACKLOG_JSON)
    if not json_path.exists():
        return  # 未迁移的旧项目，不插手
    data = load_json(json_path)
    if data is None:
        return  # json 本身坏了，交给 handle_json_write 报
    expected = render_md(data)
    actual = read_text(md_path)
    if actual is None:
        return
    if actual.replace("\r\n", "\n") == expected.replace("\r\n", "\n"):
        return

    try:
        md_path.write_text(expected, encoding="utf-8")
    except Exception:
        return
    fail(
        "[agile] PRODUCT-BACKLOG.md 是 backlog.json 的渲染产物，直接写它无效——已按当前 json 重新渲染。\n"
        "  改条目：编辑 agile-docs/backlog.json，保存后自会重新渲染本文件。\n"
        "  看统计：跑 `agile.py stats`，不需要改任何文件。"
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
    """状态不是「已关闭」的 Sprint。"""
    return [(stem, meta) for _p, stem, meta, _items in scan_sprints(root) if meta.get("状态") != "已关闭"]


def detect_stage(root: Path) -> str:
    """当前处在流程的哪一步。顺序即优先级。

    判据看重「最靠后的里程碑」，不是严格按层顺序：套件允许用户显式跳层
    （agile-backlog §0），已有条目的项目不能被判回「战略层未起步」。
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
    has_items = data is not None and any(True for _ in iter_items(data))

    if has_items:
        return "sprint" if not active_sprints(root) else "active"
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
    md_path = docs / BACKLOG_MD
    parts: list[str] = []

    sprints = scan_sprints(root)
    if sprints:
        _path, stem, meta, _items = sprints[-1]
        chunks = stem.split("-")
        seq = chunks[1] if len(chunks) > 1 else stem
        bits = [f"Sprint {seq}"]
        if meta.get("状态"):
            bits.append(meta["状态"])
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
        actual = read_text(md_path) if md_path.exists() else None
        if actual is not None and actual.replace("\r\n", "\n") != render_md(data):
            parts.append(f"⚠ {BACKLOG_MD} 与 backlog.json 不同步——跑 `agile.py render` 重新生成")

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
        f"这轮命中「{'/'.join(hits)}」。若要从零建立愿景、待办池与迭代计划，"
        "先读 `using-agile` 走初始化（先问项目画像，不写任何文件）；只是讨论技术细节就忽略本行。\n"
        "</agile-hint>",
    )


# ── 命令行 ──────────────────────────────────────────────────────────────────
USAGE = """agile.py —— Backlog 机械操作（标准库 only，零正则）

  render  [项目根]   从 agile-docs/backlog.json 渲染 PRODUCT-BACKLOG.md
  stats   [项目根]   打印统计（每次全量重算，已撤回不计入）
  check   [项目根]   结构校验 + Sprint 点数对账，有问题返回 1
  migrate [项目根]   旧版 PRODUCT-BACKLOG.md → backlog.json（json 已存在则不动）
  brief   [项目根]   打印当前阶段与每轮将要注入的内容（排查 hook 用）

  hook-post-write    hook 入口：写完文件后校验并渲染（exit 2 = 需要模型处理）
  hook-session       hook 入口：会话开始注入敏捷状态
  hook-prompt        hook 入口：每轮判断本轮要不要走敏捷流程
"""


def resolve(root_arg: str | None) -> tuple[Path, Path, Path]:
    root = Path(root_arg) if root_arg else Path.cwd()
    docs = root / DOCS_DIR
    return root, docs / BACKLOG_JSON, docs / BACKLOG_MD


def load_or_report(json_path: Path) -> dict | None:
    if not json_path.exists():
        print(f"找不到 {json_path}")
        print(f"  旧项目改造：先跑 `agile.py migrate {json_path.parent.parent}`")
        return None
    data = load_json(json_path)
    if data is None:
        print(f"{json_path} 不是合法 JSON")
        return None
    return data


def cli_render(root_arg: str | None) -> int:
    _root, json_path, md_path = resolve(root_arg)
    data = load_or_report(json_path)
    if data is None:
        return 1
    errors, warnings = validate(data)
    if errors:
        for line in errors:
            print("错误：" + line)
        return 1
    md_path.write_text(render_md(data), encoding="utf-8")
    stats = compute_stats(data)
    print(f"已渲染 {md_path}")
    print(f"  {stats['total']} 条 / {stats['points']} 点，已确认 {stats['confirmed']}")
    for line in warnings:
        print("提示：" + line)
    return 0


def cli_stats(root_arg: str | None) -> int:
    _root, json_path, _md_path = resolve(root_arg)
    data = load_or_report(json_path)
    if data is None:
        return 1
    print("\n".join(render_stats_lines(compute_stats(data))))
    return 0


def cli_check(root_arg: str | None) -> int:
    root, json_path, md_path = resolve(root_arg)
    data = load_or_report(json_path)
    if data is None:
        return 1

    errors, warnings = validate(data)
    problems: list[str] = []
    problems.extend("结构：" + line for line in errors)
    problems.extend("规范：" + line for line in warnings)
    problems.extend("跨文件：" + line for line in check_sprint_consistency(root, data))

    sync_ok = False
    if md_path.exists():
        actual = read_text(md_path)
        sync_ok = actual is not None and actual.replace("\r\n", "\n") == render_md(data)
    if not sync_ok:
        problems.append(f"同步：{md_path.name} 与 backlog.json 不一致，跑 `agile.py render`")

    if not problems:
        stats = compute_stats(data)
        print(f"通过：{stats['total']} 条 / {stats['points']} 点，Markdown 与 json 一致")
        return 0
    print(f"发现 {len(problems)} 处问题：")
    for line in problems:
        print("  · " + line)
    return 1


def cli_migrate(root_arg: str | None) -> int:
    _root, json_path, md_path = resolve(root_arg)
    if json_path.exists():
        print(f"{json_path} 已存在，不覆盖。要重新迁移请先自行移走它。")
        return 1
    text = read_text(md_path)
    if text is None:
        print(f"找不到 {md_path}，没有可迁移的旧格式")
        return 1
    data = convert_legacy_md(text)
    if not data["phases"]:
        print(f"{md_path} 里没有识别到「## 阶段 N」表格，未迁移")
        return 1

    json_path.write_text(dump_json(data), encoding="utf-8")
    md_path.write_text(render_md(data), encoding="utf-8")

    stats = compute_stats(data)
    print(f"已迁移 {md_path.name} → {json_path.name}，并把 Markdown 重渲染为产物格式")
    print(f"  {stats['total']} 条 / {stats['points']} 点，已确认 {stats['confirmed']}")
    errors, warnings = validate(data)
    for line in errors:
        print("错误：" + line)
    for line in warnings:
        print("提示：" + line)
    return 0 if not errors else 1


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
    "render": cli_render,
    "stats": cli_stats,
    "check": cli_check,
    "migrate": cli_migrate,
    "brief": cli_brief,
}


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
    _init_io()
    mode = sys.argv[1] if len(sys.argv) > 1 else "help"
    if mode.startswith("hook-"):
        # fail-open：门禁脚本自己出错时沉默退出，不能让每次编辑都弹一条错误。
        # 但 exit 2（明确的规范错误）必须原样传递，所以 SystemExit 放行。
        try:
            main(sys.argv)
        except SystemExit:
            raise
        except BaseException:
            pass
        sys.exit(0)
    sys.exit(main(sys.argv))
