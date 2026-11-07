#!/usr/bin/env python3
"""agile 套件的机械部分：Backlog 结构校验、统计、渲染、旧格式迁移、hook 入口。

为什么存在：点数和条目统计原先靠 agent 每次现场写脚本兑现，每次都不一样。
计算这件事不该交给模型。

设计取舍
--------
* **backlog.json 只装待办池。** 风险 / 发布 / 决策是三个可选小文件
  （risks.json / releases.json / decisions.json），各管一个聚合、缺省 = 能力
  未启用——不并进 backlog.json，避免一个上帝文件。历史上的 PRODUCT-BACKLOG.md
  渲染产物已随 5.6.0 退役（人读视图 = 问 agent 或 `agile.py stats / report`），
  脚本因此从不需要解析 Markdown，也不必写正则去容错列数漂移、全角空格、
  `\\|` 转义这些迟早会出问题的地方。
* **标准库 only，零正则。** 结构化数据用 json 模块，行级判断用 startswith / split。
* **hook stdout 只说 JSON。** CC 与 ZCode 都从 stdout 解析 hook 结果，但 ZCode 对
  不以 `{` 开头的输出**静默忽略**（= 永不注入），所以 hook 入口的 stdout 不许混任何
  日志或纯文本；要注入就走 `hookSpecificOutput.additionalContext`，要阻断就走顶层
  `decision: "block"` + `reason`（两家的交集形态）。
* **fail-open，且有意退出码只有 0。** 脚本随插件分发到别人机器上，任何未预期异常
  都变成沉默退出 0。hook 有意非零退出会破坏 hooks.json 里 `python || python3`
  的兜底语义（`||` 只该在解释器缺失时轮到第二个），所以问题清单走 stdout JSON。
* **长期待办按日缓存，缓存与提醒额度互不失效。** 年龄快照（汇总行 + 至多 3 条
  提醒明细）按「自然日 + backlog/Sprint 文件指纹（mtime_ns / size）」落在临时
  目录：同日同文件不再重算，PostToolUse 写盘后主动删，外部改动靠指纹兜底；
  mtime 只判缓存新鲜度，绝不参与年龄计算（年龄唯一来源是 created_at）。缓存
  失效不删当日提醒 marker——文件怎么变，同日最多展开一次。review/stats/check
  永远读实时文件，不走这份缓存。
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
import traceback
from datetime import date
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

TYPES = ("技术", "功能", "缺陷")
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
ID_PREFIXES = ("T-", "F-", "B-")
QUOTES = "\"'“”‘’"
POINT_BRACKETS = (("(", ")"), ("（", "）"))
FEEDBACK_TYPES = ("reason", "issue", "decision")
REVIEW_AGE_DAYS = 30
DATE_FIELDS = ("created_at", "last_reviewed_at")
# 年龄快照缓存的结构版本：快照字段语义变化时递增，旧缓存整体作废重算。
AGE_CACHE_VERSION = 1

# 执行层三个可选小文件：各管一个聚合（不并进 backlog.json，那只是待办池），
# 缺省 = 该能力未启用。字段定义见 agile-backlog/references/ 下
# risk-rules / release-rules / decision-rules，流程全貌见 using-agile/references/workflow.md。
RISKS_JSON = "risks.json"
RELEASES_JSON = "releases.json"
DECISIONS_JSON = "decisions.json"
SIDE_FILES = (RISKS_JSON, RELEASES_JSON, DECISIONS_JSON)
RISK_STATUSES = ("活跃", "已发生", "已解除", "已接受")
RISK_HIT = "已发生"
RELEASE_STATUSES = ("规划中", "已发布", "已取消")
RELEASE_PUBLISHED = "已发布"
RELEASE_CHECKS = ("rollback", "migration", "notice")
DECISION_OUTCOMES = ("做", "不做")


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


def is_seq_id(value, prefix: str) -> bool:
    """R-/D- 这类带前缀序号 ID 的通用判定，与 is_item_id 同口径。"""
    if not isinstance(value, str) or not value.startswith(prefix):
        return False
    tail = value[len(prefix):]
    return 3 <= len(tail) <= 4 and tail.isdigit()


def is_int(value) -> bool:
    """布尔是 int 的子类：`true` 会被 isinstance(..., int) 当成 1 混过整数校验。"""
    return isinstance(value, int) and not isinstance(value, bool)


def parse_iso_date(value) -> date | None:
    """只接受跨 Python 版本行为一致的 YYYY-MM-DD，其它值交给校验层报出。"""
    if not isinstance(value, str) or len(value) != 10:
        return None
    if value[4] != "-" or value[7] != "-":
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def validate(data: dict, today: date | None = None) -> tuple[list[str], list[str]]:
    """返回 (errors, warnings)。缺失日期兼容存量，写错的日期仍是结构错误。"""
    today = today or date.today()
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

            parsed_dates: dict[str, date] = {}
            for field in DATE_FIELDS:
                raw_date = item.get(field)
                if raw_date is None:
                    continue
                parsed = parse_iso_date(raw_date)
                if parsed is None:
                    errors.append(f"{ident} 的 {field} 必须是 YYYY-MM-DD，当前是 {raw_date!r}")
                    continue
                parsed_dates[field] = parsed
                if parsed > today:
                    errors.append(f"{ident} 的 {field} 不能晚于今天（{today.isoformat()}）")
            created = parsed_dates.get("created_at")
            reviewed = parsed_dates.get("last_reviewed_at")
            if created and reviewed and reviewed < created:
                errors.append(f"{ident} 的 last_reviewed_at 不能早于 created_at")

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


# ── 执行层小文件（risks / releases / decisions）校验 ─────────────────────────
def validate_risks(data: dict, today: date) -> tuple[list[str], list[str]]:
    """risks.json 结构校验。语义规则（不打分、不自动升级）归 risk-rules.md，脚本只查结构。"""
    errors: list[str] = []
    warnings: list[str] = []
    risks = data.get("risks")
    if not isinstance(risks, list):
        return ['缺少 risks 数组——顶层必须是 {"schema": 1, "risks": [{...}]}'], []
    seen: set[str] = set()
    for index, risk in enumerate(risks, start=1):
        if not isinstance(risk, dict):
            errors.append(f"risks[{index}] 不是对象")
            continue
        ident = risk.get("id")
        if not is_seq_id(ident, "R-"):
            errors.append(f"risks[{index}] 的 id「{ident}」不合规（R- + 3~4 位数字）")
            continue
        if ident in seen:
            errors.append(f"{ident} 重复出现")
        seen.add(ident)
        for field in ("title", "status", "impact", "created_at"):
            if not risk.get(field):
                errors.append(f"{ident} 缺少必填字段 {field}")
        status = risk.get("status")
        if status and status not in RISK_STATUSES:
            errors.append(f"{ident} 状态「{status}」不在 {'/'.join(RISK_STATUSES)}")
        raw = risk.get("created_at")
        if raw is not None:
            parsed = parse_iso_date(raw)
            if parsed is None:
                errors.append(f"{ident} 的 created_at 必须是 YYYY-MM-DD，当前是 {raw!r}")
            elif parsed > today:
                errors.append(f"{ident} 的 created_at 不能晚于今天（{today.isoformat()}）")
        if status == RISK_HIT and not risk.get("hit_ref"):
            # 允许「先标已发生、下一拍补 hit_ref」的分步写，所以提示不阻断。
            warnings.append(f"{ident} 已发生但还没填 hit_ref（转出的条目 ID）")
        hit = risk.get("hit_ref")
        if hit is not None and not is_item_id(hit):
            errors.append(f"{ident} 的 hit_ref「{hit}」不是条目 ID（T-/F-/B-）")
    return errors, warnings


def validate_releases(data: dict, today: date) -> tuple[list[str], list[str]]:
    """releases.json 结构校验。检查单防漏事不做门禁，checks 未全过只提示。"""
    errors: list[str] = []
    warnings: list[str] = []
    releases = data.get("releases")
    if not isinstance(releases, list):
        return ['缺少 releases 数组——顶层必须是 {"schema": 1, "releases": [{...}]}'], []
    seen: set[str] = set()
    for index, rel in enumerate(releases, start=1):
        if not isinstance(rel, dict):
            errors.append(f"releases[{index}] 不是对象")
            continue
        ident = rel.get("id")
        if not isinstance(ident, str) or not ident.strip():
            errors.append(f"releases[{index}] 缺少 id（版本号即 ID）")
            continue
        if ident in seen:
            errors.append(f"release {ident} 重复出现")
        seen.add(ident)
        if not rel.get("title"):
            errors.append(f"release {ident} 缺少 title")
        status = rel.get("status")
        if status and status not in RELEASE_STATUSES:
            errors.append(f"release {ident} 状态「{status}」不在 {'/'.join(RELEASE_STATUSES)}")
        items = rel.get("items")
        if not isinstance(items, list) or not items:
            errors.append(f"release {ident} 的 items 必须是非空数组（条目 ID）")
        else:
            for entry in items:
                if not is_item_id(entry):
                    errors.append(f"release {ident} 的 items 含非法 ID「{entry}」（T-/F-/B-）")
        checks = rel.get("checks")
        if not isinstance(checks, dict):
            errors.append(f"release {ident} 缺少 checks（固定三键布尔 {'/'.join(RELEASE_CHECKS)}）")
        else:
            for key in RELEASE_CHECKS:
                if not isinstance(checks.get(key), bool):
                    errors.append(f"release {ident} 的 checks.{key} 必须是 true/false")
            extra = [key for key in checks if key not in RELEASE_CHECKS]
            if extra:
                warnings.append(f"release {ident} 的 checks 有多余键 {extra}（只认 {'/'.join(RELEASE_CHECKS)}）")
        raw = rel.get("released_at")
        if raw is not None:
            parsed = parse_iso_date(raw)
            if parsed is None:
                errors.append(f"release {ident} 的 released_at 必须是 YYYY-MM-DD，当前是 {raw!r}")
            elif parsed > today and status == RELEASE_PUBLISHED:
                # 规划中的 released_at 是计划发布日、允许未来；已发布才是实际日期。
                errors.append(f"release {ident} 已发布，released_at 不能晚于今天（{today.isoformat()}）")
        if status == RELEASE_PUBLISHED:
            if raw is None:
                warnings.append(f"release {ident} 已发布但没有 released_at")
            if isinstance(checks, dict) and any(checks.get(key) is not True for key in RELEASE_CHECKS):
                warnings.append(f"release {ident} 已发布但 checks 有未确认项（提示不阻断）")
    return errors, warnings


def validate_decisions(data: dict, today: date) -> tuple[list[str], list[str]]:
    """decisions.json 结构校验。只记结果不记过程归 decision-rules.md。"""
    errors: list[str] = []
    warnings: list[str] = []
    decisions = data.get("decisions")
    if not isinstance(decisions, list):
        return ['缺少 decisions 数组——顶层必须是 {"schema": 1, "decisions": [{...}]}'], []
    seen: set[str] = set()
    for index, dec in enumerate(decisions, start=1):
        if not isinstance(dec, dict):
            errors.append(f"decisions[{index}] 不是对象")
            continue
        ident = dec.get("id")
        if not is_seq_id(ident, "D-"):
            errors.append(f"decisions[{index}] 的 id「{ident}」不合规（D- + 3~4 位数字）")
            continue
        if ident in seen:
            errors.append(f"{ident} 重复出现")
        seen.add(ident)
        for field in ("decision", "outcome", "basis", "date"):
            if not dec.get(field):
                errors.append(f"{ident} 缺少必填字段 {field}")
        outcome = dec.get("outcome")
        if outcome and outcome not in DECISION_OUTCOMES:
            errors.append(f"{ident} 的 outcome「{outcome}」不在 {'/'.join(DECISION_OUTCOMES)}")
        raw = dec.get("date")
        if raw is not None:
            parsed = parse_iso_date(raw)
            if parsed is None:
                errors.append(f"{ident} 的 date 必须是 YYYY-MM-DD，当前是 {raw!r}")
            elif parsed > today:
                errors.append(f"{ident} 的 date 不能晚于今天（{today.isoformat()}）")
        refs = dec.get("refs")
        if refs is not None and not isinstance(refs, list):
            errors.append(f"{ident} 的 refs 必须是数组")
    return errors, warnings


SIDE_VALIDATORS = {
    RISKS_JSON: validate_risks,
    RELEASES_JSON: validate_releases,
    DECISIONS_JSON: validate_decisions,
}


def check_side_refs(root: Path, data: dict, name: str) -> list[str]:
    """单个小文件对 backlog 条目的引用对账（跨文件）。

    只查指定文件：写 risks.json 时把 releases 的陈年引用也报出来是噪音。
    引用允许多步补（先登记风险后建条目），所以这条是提示级，不进结构错误。
    """
    known = {item["id"] for _phase, item in iter_items(data) if item.get("id")}
    payload = load_json(root / DOCS_DIR / name)
    if not isinstance(payload, dict):
        return []
    problems: list[str] = []
    if name == RISKS_JSON:
        for risk in payload.get("risks") or []:
            if not isinstance(risk, dict):
                continue
            hit = risk.get("hit_ref")
            if hit and hit not in known:
                problems.append(f"{risk.get('id', '?')} 的 hit_ref 引用 {hit}，backlog.json 里没有这个条目")
    elif name == RELEASES_JSON:
        for rel in payload.get("releases") or []:
            if not isinstance(rel, dict):
                continue
            for entry in rel.get("items") or []:
                if is_item_id(entry) and entry not in known:
                    problems.append(f"release {rel.get('id', '?')} 的 items 引用 {entry}，backlog.json 里没有这个条目")
    elif name == DECISIONS_JSON:
        for dec in payload.get("decisions") or []:
            if not isinstance(dec, dict):
                continue
            for entry in dec.get("refs") or []:
                if is_item_id(entry) and entry not in known:
                    problems.append(f"{dec.get('id', '?')} 的 refs 引用 {entry}，backlog.json 里没有这个条目")
    return problems


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


def collect_backlog_age(data: dict, sprints, today: date) -> dict:
    """统一计算长期未完成与待复核；活跃 Sprint 条目排除，日期未知单列。"""
    planned_ids = {ident for _p, _stem, _meta, items in sprints for ident, _points in items}
    active_ids = {
        ident
        for _p, _stem, meta, items in sprints
        if sprint_status(meta) != "closed"
        for ident, _points in items
    }
    aged: list[dict] = []
    due: list[dict] = []
    unknown: list[dict] = []

    for _phase, item in iter_items(data):
        if item.get("status") != TODO_STATUS:
            continue
        ident = str(item.get("id") or "?")
        if ident in active_ids:
            continue
        base = {
            "id": ident,
            "title": str(item.get("title") or ""),
            "priority": str(item.get("priority") or "未标"),
            # Sprint 归档后活扫描看不见它的任务清单，「曾纳入」靠闭环同步时
            # 落在条目上的 planned_sprints 戳记兜底（backlog-rules §二）。
            "ever_planned": ident in planned_ids or bool(item.get("planned_sprints")),
        }
        created = parse_iso_date(item.get("created_at"))
        if created is None:
            unknown.append(base)
            continue
        age = (today - created).days
        if age < 0:
            unknown.append(base)
            continue
        if age < REVIEW_AGE_DAYS:
            continue
        reviewed = parse_iso_date(item.get("last_reviewed_at"))
        review_valid = reviewed is not None and created <= reviewed <= today
        needs_review = not review_valid or (today - reviewed).days >= REVIEW_AGE_DAYS
        row = {
            **base,
            "age": age,
            "created_at": created.isoformat(),
            "last_reviewed_at": reviewed.isoformat() if reviewed else None,
            "due": needs_review,
        }
        aged.append(row)
        if needs_review:
            due.append(row)

    sort_key = lambda row: (-row["age"], row["id"])
    aged.sort(key=sort_key)
    due.sort(key=sort_key)
    unknown.sort(key=lambda row: row["id"])
    return {"aged": aged, "due": due, "unknown": unknown}


def backlog_age_summary(report: dict) -> list[str]:
    """把年龄报告压成有界状态行；条目明细只进 review 或当日首次提醒。"""
    lines: list[str] = []
    aged = report["aged"]
    if aged:
        lines.append(
            f"长期未完成 {len(aged)} 条（≥{REVIEW_AGE_DAYS} 天，最久 {aged[0]['age']} 天；"
            f"待复核 {len(report['due'])} 条）"
        )
    if report["unknown"]:
        lines.append(f"创建时间未知或非法 {len(report['unknown'])} 条（review 查看）")
    return lines


def render_review_lines(report: dict) -> list[str]:
    """渲染完整只读复核清单，不改变任何条目状态。"""
    aged = report["aged"]
    lines = [
        f"长期未完成：{len(aged)} 条（≥{REVIEW_AGE_DAYS} 天，不含活跃 Sprint；待复核 {len(report['due'])} 条）"
    ]
    for row in aged:
        history = "曾纳入 Sprint" if row["ever_planned"] else "从未纳入 Sprint"
        reviewed = row["last_reviewed_at"] or "从未复核"
        due = "待复核" if row["due"] else "近期已复核"
        lines.append(
            f"- {row['id']} {row['title']}｜{row['priority']}｜立项 {row['age']} 天｜"
            f"{history}｜{reviewed}｜{due}"
        )

    unknown = report["unknown"]
    if unknown:
        lines.append(f"创建时间未知或非法：{len(unknown)} 条（不参与年龄判定）")
        for row in unknown:
            lines.append(f"- {row['id']} {row['title']}｜{row['priority']}")
    lines.append("提示：年龄只是复核信号；保留、调整或撤回均由用户裁决。")
    return lines


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


def render_side_lines(root: Path) -> list[str]:
    """三个小文件的统计行；文件不存在 = 能力未启用，不输出占位行。"""
    docs = root / DOCS_DIR
    lines: list[str] = []
    specs = (
        (RISKS_JSON, "risks", "风险"),
        (RELEASES_JSON, "releases", "发布"),
        (DECISIONS_JSON, "decisions", "决策"),
    )
    for name, key, label in specs:
        payload = load_json(docs / name) if (docs / name).exists() else None
        if not isinstance(payload, dict):
            continue
        rows = [row for row in (payload.get(key) or []) if isinstance(row, dict)]
        buckets: dict = {}
        for row in rows:
            bucket = str(row.get("status") or row.get("outcome") or "未标")
            buckets[bucket] = buckets.get(bucket, 0) + 1
        joined = "；".join(f"{bucket} = {count}" for bucket, count in sorted(buckets.items()))
        lines.append(f"- {label}：{len(rows)} 条" + (f"（{joined}）" if joined else ""))
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


def iter_sprint_files(root: Path):
    """SPRINT_DIRS 下平铺的 sprint-*.md，按（目录顺序, 文件名）稳定产出。

    只扫一层、不进子目录：`archive/`（闭环归档位）必须对状态检测、点数对账、
    指纹全部不可见。这个平铺契约由全部调用方共享，只在这里定义一次。
    """
    for rel in SPRINT_DIRS:
        directory = root / rel
        if not directory.is_dir():
            continue
        try:
            entries = sorted(directory.iterdir())
        except Exception:
            continue
        for path in entries:
            if path.name.startswith("sprint-") and path.name.endswith(".md"):
                yield path


def iter_done_files(root: Path):
    """SPRINT_DIRS 下平铺的 *.done.yaml；`.done.processed.yaml` 后缀不同，天然不含。"""
    for rel in SPRINT_DIRS:
        directory = root / rel
        if not directory.is_dir():
            continue
        try:
            entries = sorted(directory.iterdir())
        except Exception:
            continue
        for path in entries:
            if path.name.endswith(".done.yaml"):
                yield path


def scan_sprints(root: Path):
    """返回 [(文件路径, 文件主名, 元信息, 任务清单)]，按序号升序。

    每次调用读全部 Sprint 文件。长期待办的年龄快照已按日缓存（见 age_snapshot），
    这里剩下的调用方是状态摘要与阶段判定；Sprint 数到 50 上下才开始有可感知
    延迟，先不为它们再加一层缓存。
    """
    found = []
    for path in iter_sprint_files(root):
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
    for path in iter_done_files(root):
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
        # 失效先于校验：写盘那一刻快照就旧了，校验是否通过不影响这个事实。
        invalidate_age_cache(root_of(path))
        handle_json_write(path)
    elif path.name in SIDE_FILES:
        handle_side_write(path)
    elif path.name.endswith(".done.yaml"):
        handle_done_write(path, root)
    elif path.suffix == ".md" and path.name.startswith("sprint-") and path.parent.name == "sprints":
        # 只认 sprints/ 下的 sprint-*.md：项目根放一份 sprint-notes.md 不该被当成
        # Sprint 文件质问，这也是 scan_sprints 的扫描范围。
        base = path.parent.parent
        invalidate_age_cache(base.parent if base.name == DOCS_DIR else base)
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


def handle_side_write(side_path: Path) -> None:
    """risks / releases / decisions 写后校验：结构错 block，引用问题提示。

    与 backlog.json 同口径——机器契约、整文件写入，结构错误当场拦；
    跨文件引用允许多步补（先登记后建条目），提示不阻断。
    """
    label = side_path.name
    text = read_text(side_path)
    if text is None:
        return
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        emit_block(
            f"[agile] {label} 不是合法 JSON，本文件必须机器可读。\n"
            f"  第 {exc.lineno} 行第 {exc.colno} 列：{exc.msg}\n"
            "  常见原因：写了注释、结尾多了逗号、用了中文引号、字符串里没转义换行。"
        )
        return
    if not isinstance(data, dict):
        emit_block(f"[agile] {label} 顶层必须是对象。")
        return
    errors, warnings = SIDE_VALIDATORS[label](data, date.today())
    if errors:
        listed = "\n".join("  · " + line for line in errors)
        emit_block(
            f"[agile] {label} 结构不合规（{len(errors)} 处）：\n{listed}\n"
            "  字段说明见 agile-backlog/references/ 下对应 rules 文件。"
        )
        return
    notes = list(warnings)
    backlog = load_json(root_of(side_path) / DOCS_DIR / BACKLOG_JSON)
    if isinstance(backlog, dict):
        notes.extend(check_side_refs(root_of(side_path), backlog, label))
    if notes:
        listed = "\n".join("  · " + line for line in notes)
        emit_context(
            "PostToolUse",
            f"[agile] {label} 已通过结构校验，另有 {len(notes)} 处待处理：\n{listed}",
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
    return [p.name[: -len(".done.yaml")] for p in iter_done_files(root)]


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


# ── 长期待办当日快照（日缓存，只省重复计算、不改任何口径） ──────────────────────
def age_cache_path(root: Path) -> Path:
    """快照按项目根分文件，放临时目录；与提醒 marker 同目录但互不影响。"""
    digest = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"agile-age-{digest}.json"


def age_fingerprint(root: Path) -> list[list] | None:
    """缓存新鲜度指纹：backlog.json 与全部 Sprint md 的 (相对名, mtime_ns, size)。

    mtime 只回答「缓存还新鲜吗」，绝不参与年龄计算——立项年龄的唯一来源是
    created_at（backlog-rules §五），mtime 会随任何一次无关写动跳动。列表结构
    与 JSON 往返后的形态一致，相等比较才有意义。backlog.json 不在 → None。
    """
    files: list[list] = []
    json_path = root / DOCS_DIR / BACKLOG_JSON
    try:
        stat = json_path.stat()
    except OSError:
        return None
    files.append([BACKLOG_JSON, stat.st_mtime_ns, stat.st_size])
    for path in iter_sprint_files(root):
        try:
            stat = path.stat()
        except OSError:
            continue
        files.append([path.relative_to(root).as_posix(), stat.st_mtime_ns, stat.st_size])
    return files


def load_age_cache(root: Path, today: date, fingerprint: list) -> dict | None:
    """读当日快照；文件缺失、损坏、跨日、版本不符或指纹变化都返回 None（= 重算）。"""
    try:
        raw = json.loads(age_cache_path(root).read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(raw, dict) or raw.get("version") != AGE_CACHE_VERSION:
        return None
    if raw.get("day") != today.isoformat() or raw.get("fingerprint") != fingerprint:
        return None
    summary = raw.get("summary")
    items = raw.get("notice_items")
    due_count = raw.get("due_count")
    if not isinstance(summary, list) or not all(isinstance(line, str) for line in summary):
        return None
    if not isinstance(items, list) or not all(isinstance(line, str) for line in items):
        return None
    if not is_int(due_count) or due_count < 0:
        return None
    return {"summary": summary, "due_count": due_count, "notice_items": items}


def save_age_cache(root: Path, today: date, fingerprint: list, payload: dict) -> None:
    """写快照（没有待复核也写负缓存）；失败静默——缓存只是加速器，不是事实源。"""
    target = age_cache_path(root)
    scratch = target.with_name(f"{target.name}.{os.getpid()}.tmp")
    try:
        body = {"version": AGE_CACHE_VERSION, "day": today.isoformat(),
                "fingerprint": fingerprint, **payload}
        scratch.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
        os.replace(scratch, target)
    except Exception:
        try:
            scratch.unlink()
        except OSError:
            pass


def invalidate_age_cache(root: Path) -> None:
    """PostToolUse 写盘后主动失效。删不掉也由指纹兜底；绝不碰提醒 marker。"""
    try:
        age_cache_path(root).unlink()
    except OSError:
        pass


def render_notice_items(due: list[dict]) -> list[str]:
    """复核提醒的至多 3 条明细，与 review 清单同一种行格式。"""
    lines = []
    for row in due[:3]:
        history = "曾纳入 Sprint" if row["ever_planned"] else "从未纳入 Sprint"
        lines.append(f"- {row['id']} {row['title']}｜{row['priority']}｜立项 {row['age']} 天｜{history}")
    return lines


def age_snapshot(root: Path, today: date) -> dict | None:
    """当日长期待办快照：汇总行 / 待复核数 / 提醒明细，两个 hook 路径共用。

    每天首次或文件指纹变化时重算一次并写缓存，其余轮次直接命中——状态摘要与
    复核提醒从此共用这一份，不再各自 load + scan + 计算。backlog 缺失或读不出
    → None（与 describe_state 原行为一致：没有年龄行可注入）。
    """
    fingerprint = age_fingerprint(root)
    if fingerprint is None:
        return None
    cached = load_age_cache(root, today, fingerprint)
    if cached is not None:
        return cached
    data = load_json(root / DOCS_DIR / BACKLOG_JSON)
    if data is None:
        return None
    report = collect_backlog_age(data, scan_sprints(root), today)
    payload = {
        "summary": backlog_age_summary(report),
        "due_count": len(report["due"]),
        "notice_items": render_notice_items(report["due"]),
    }
    save_age_cache(root, today, fingerprint, payload)
    return payload


def build_state_block(root: Path, notify_review: bool = False) -> str:
    """每轮 / 每次会话注入状态；只有用户发言时才展开当日首次复核提醒。"""
    snapshot = age_snapshot(root, date.today())
    parts = describe_state(root, snapshot)
    body = "｜".join(parts) if parts else "agile-docs/ 已存在"
    stage = detect_stage(root)
    briefs = load_briefs()
    brief = briefs.get(stage, "") if stage else ""
    if not brief:
        # 故意显眼：文案文件缺失或被改名时，要让模型知道自己在裸奔，而不是静默降级。
        brief = f"阶段说明缺失（{BRIEF_REL} 里没有 [{stage or '?'}] 块），按 `using-agile` 自行判断该走哪一步。"
    lines = ["<agile-state>", body, brief]
    if notify_review:
        notice = claim_review_notice(root, briefs, snapshot)
        if notice:
            lines.append(notice)
    lines.extend([ROUTING_LINE, "</agile-state>"])
    return "\n".join(lines)


def describe_state(root: Path, snapshot: dict | None = None) -> list[str]:
    """Sprint / 回填 / Backlog / ADR 的一行式摘要，两个 hook 共用。

    长期待办汇总行来自当日快照（age_snapshot，可能直接命中缓存），这里不再
    重复计算——原先状态摘要与复核提醒各算一遍年龄，是每轮三趟扫描的来源之一。
    """
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
        if snapshot:
            parts.extend(snapshot["summary"])

    adr_text = read_text(docs / ADR_MD)
    if adr_text:
        total, proposed = parse_adr(adr_text)
        if total:
            parts.append(f"ADR {total} 条（{proposed} 条 Proposed 待拍板）" if proposed else f"ADR {total} 条")

    risks = load_json(docs / RISKS_JSON) if (docs / RISKS_JSON).exists() else None
    if isinstance(risks, dict):
        rows = [row for row in (risks.get("risks") or []) if isinstance(row, dict)]
        active = sum(1 for row in rows if row.get("status") == "活跃")
        parts.append(f"风险 {active} 活跃 / 共 {len(rows)}")
    releases = load_json(docs / RELEASES_JSON) if (docs / RELEASES_JSON).exists() else None
    if isinstance(releases, dict):
        rows = [row for row in (releases.get("releases") or []) if isinstance(row, dict)]
        planned = sum(1 for row in rows if row.get("status") == "规划中")
        parts.append(f"发布 {planned} 规划中 / 共 {len(rows)}")
    decisions = load_json(docs / DECISIONS_JSON) if (docs / DECISIONS_JSON).exists() else None
    if isinstance(decisions, dict):
        parts.append(f"决策 {len(decisions.get('decisions') or [])} 条")

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


def review_marker(root: Path) -> Path:
    """长期待办按项目 + 本地日期去重，避免换会话在同一天反复提醒。"""
    key = str(root) + time.strftime("%Y-%m-%d")
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"agile-review-{digest}.marker"


def claim_day_marker(marker: Path) -> bool:
    """原子领取当日额度：O_CREAT|O_EXCL 由系统保证唯一，并发会话只有一个成功。

    建不了文件（临时目录不可写等）也返回 False——宁可漏一次提醒，不重复打扰。
    """
    try:
        fd = os.open(str(marker), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except OSError:
        return False
    try:
        os.write(fd, b"1")
    except OSError:
        pass
    finally:
        os.close(fd)
    return True


def claim_review_notice(root: Path, briefs: dict[str, str], snapshot: dict | None) -> str:
    """领取当日提醒额度并展开至多三条明细；年龄快照由 build_state_block 共享传入。"""
    if not snapshot or not snapshot["due_count"]:
        return ""
    if not claim_day_marker(review_marker(root)):
        return ""

    brief = briefs.get("review", "")
    if not brief:
        brief = f"长期待办提醒说明缺失（{BRIEF_REL} 里没有 [review] 块），按 agile-backlog 的长期待办复核流程处理。"
    lines = ["<agile-review>", brief, "待复核条目（至多 3 条）："]
    lines.extend(snapshot["notice_items"])
    rest = snapshot["due_count"] - len(snapshot["notice_items"])
    if rest > 0:
        lines.append(f"其余 {rest} 条见 `agile.py review`")
    lines.append("</agile-review>")
    return "\n".join(lines)


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
        # 长期待办明细只在用户发言时展开，避免 SessionStart 提前消耗当日提醒额度。
        emit_context("UserPromptSubmit", build_state_block(root, notify_review=True))
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


# ── Sprint 历史与趋势（trend / report 的数据层） ─────────────────────────────
def iter_history_sprint_files(root: Path):
    """flat + archive/ 两层的 sprint-*.md，只给 trend / report 用。

    scan_sprints 的平铺契约是**状态检测口径**——archive 必须对检测与对账不可见；
    趋势恰恰消费归档历史，所以单独一条遍历，不共用平铺契约。
    """
    for rel in SPRINT_DIRS:
        for directory in (root / rel, root / rel / "archive"):
            if not directory.is_dir():
                continue
            try:
                entries = sorted(directory.iterdir())
            except Exception:
                continue
            for path in entries:
                if path.name.startswith("sprint-") and path.name.endswith(".md"):
                    yield path


def parse_status_suggestions(text: str) -> tuple[list[str], list[str]]:
    """条目状态建议行：`- T-001：已完成（…）` / `- T-003：移至下个Sprint（…）`。

    行级扫描，只认「- ID：」开头且 ID 合规的行——任务清单行没有冒号，天然不
    匹配。这是人工确认关闭的 Sprint 在没有 .done 文件时的完成/顺延来源。
    """
    completed: list[str] = []
    moved: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        head, sep, tail = split_kv(stripped[2:].strip())
        if not sep or not is_item_id(head):
            continue
        if tail.startswith("已完成"):
            completed.append(head)
        elif tail.startswith("移至"):
            moved.append(head)
    return completed, moved


def find_done_for(sprint_path: Path) -> Path | None:
    for suffix in (".done.processed.yaml", ".done.yaml"):
        candidate = sprint_path.with_name(sprint_path.stem + suffix)
        if candidate.exists():
            return candidate
    return None


def sprint_history(root: Path) -> list[dict]:
    """已关闭 Sprint 的承诺/完成/顺延明细，按序号升序。

    完成来源优先 .done(.processed).yaml（结构化回填），人工确认关闭的 Sprint
    没有 done 文件，退回「条目状态建议」行。只收状态 closed 的 Sprint。
    """
    rows: list[dict] = []
    for path in iter_history_sprint_files(root):
        text = read_text(path)
        if text is None:
            continue
        if sprint_status(parse_sprint_meta(text)) != "closed":
            continue
        done_path = find_done_for(path)
        if done_path is not None:
            done = parse_done(read_text(done_path) or "")
            completed, moved = list(done["completed"]), list(done["moved_next"])
            source = "done"
        else:
            completed, moved = parse_status_suggestions(text)
            source = "manual"
        rows.append({
            "stem": path.stem,
            "items": parse_sprint_items(text),
            "completed": completed,
            "moved_next": moved,
            "source": source,
        })
    rows.sort(key=lambda row: sprint_seq(row["stem"]))
    return rows


def render_trend_lines(root: Path, compact: bool = False) -> list[str]:
    """Sprint 趋势：承诺/完成点、完成率、顺延与反复顺延。compact 只出汇总行。"""
    rows = sprint_history(root)
    if not rows:
        return ["没有已关闭的 Sprint，暂无趋势。"]
    lines: list[str] = [] if compact else [f"Sprint 趋势（已关闭 {len(rows)} 个）："]
    done_points: list[int] = []
    moved_counts: dict[str, int] = {}
    for row in rows:
        committed = {ident: points for ident, points in row["items"]}
        done_ids = [ident for ident in row["completed"] if ident in committed]
        moved_ids = [ident for ident in row["moved_next"] if ident in committed]
        for ident in moved_ids:
            moved_counts[ident] = moved_counts.get(ident, 0) + 1
        all_points = sum(points or 0 for points in committed.values())
        c_points = sum(committed[ident] or 0 for ident in done_ids)
        if all_points:
            done_points.append(c_points)
            rate = f"承诺 {all_points} 点 / 完成 {c_points} 点"
        else:
            rate = f"条目 {len(done_ids)}/{len(committed)} 完成"
        if not compact:
            lines.append(f"- {row['stem']}：{rate}，{len(moved_ids)} 顺延（{row['source']}）")
    if done_points:
        recent = done_points[-3:]
        avg = sum(recent) / len(recent)
        lines.append(f"近 {len(recent)} 个 Sprint 平均完成 {avg:.1f} 点（velocity）")
    repeated = sorted(ident for ident, count in moved_counts.items() if count >= 2)
    if repeated:
        lines.append(f"反复顺延（≥2 次，估点/范围信号）：{'、'.join(repeated)}")
    return lines


def render_report_lines(root: Path) -> list[str]:
    """一页纸状态（stdout，不落文件）：战略/Backlog/风险/发布/决策/趋势。"""
    docs = root / DOCS_DIR
    parts: list[str] = ["agile 状态一页纸"]

    bits = [
        f"VISION {'✅' if (docs / 'VISION.md').exists() else '❌'}",
        f"ARCHITECTURE {'✅' if (docs / 'ARCHITECTURE.md').exists() else '❌'}",
    ]
    adr_text = read_text(docs / ADR_MD)
    if adr_text:
        total, proposed = parse_adr(adr_text)
        bits.append(f"ADR {total} 条" + (f"（{proposed} Proposed 待拍板）" if proposed else ""))
    else:
        bits.append("ADR ❌")
    parts.append("- 战略：" + " / ".join(bits))

    vision_text = read_text(docs / "VISION.md")
    if vision_text:
        for line in vision_text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                parts.append("- 定位：" + stripped[:40] + ("…" if len(stripped) > 40 else ""))
                break

    sprints = scan_sprints(root)
    if sprints:
        _path, stem, meta, _items = sprints[-1]
        parts.append(f"- Sprint：{stem} {SPRINT_LABELS[sprint_status(meta)]}")
    pending = pending_backfills(root)
    if pending:
        parts.append(f"- 待回填：{len(pending)} 个")

    data, problem = read_backlog(docs / BACKLOG_JSON)
    if data is not None:
        stats = compute_stats(data)
        parts.append(f"- Backlog：{stats['total']} 条 / {stats['points']} 点（已确认 {stats['confirmed']}）")
        for line in backlog_age_summary(collect_backlog_age(data, sprints, date.today())):
            parts.append("  " + line)
    else:
        parts.append(f"- Backlog：{problem}")

    for line in render_side_lines(root):
        parts.append(line)
    decisions = load_json(docs / DECISIONS_JSON) if (docs / DECISIONS_JSON).exists() else None
    if isinstance(decisions, dict):
        recent = [row for row in (decisions.get("decisions") or []) if isinstance(row, dict)][-3:]
        for row in recent:
            parts.append(f"  最近：{row.get('id')} {row.get('decision')}（{row.get('outcome')}）")

    for line in render_trend_lines(root, compact=True):
        parts.append("- " + line)
    return parts


# ── 命令行 ──────────────────────────────────────────────────────────────────
USAGE = """agile.py —— Backlog 机械操作（标准库 only，零正则）

  stats   [项目根]   打印统计（每次全量重算，已撤回不计入；backlog.json 只装待办池）
  review  [项目根]   只读列出长期未完成、Sprint 历史与复核状态
  check   [项目根]   结构校验 + Sprint 点数对账 + 回填内容 + risks/releases/decisions，有问题返回 1
  trend   [项目根]   已关闭 Sprint 趋势：承诺/完成点、顺延与反复顺延条目
  report  [项目根]   一页纸状态：战略/Backlog/风险/发布/决策/趋势
  brief   [项目根]   打印当前阶段与每轮基础注入原文（排查 hook 用）

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
    root, json_path, _md_path = resolve(root_arg)
    data, problem = read_backlog(json_path)
    if data is None:
        print(problem)
        print("  旧表格格式：由 agent 按 agile-backlog/references/backlog-rules.md §七 一次性转写")
        return 1
    print("\n".join(render_stats_lines(compute_stats(data))))
    report = collect_backlog_age(data, scan_sprints(root), date.today())
    for line in backlog_age_summary(report):
        print("- " + line)
    for line in render_side_lines(root):
        print(line)
    return 0


def cli_review(root_arg: str | None) -> int:
    """打印长期待办完整清单；只读，有待复核条目也不返回失败。"""
    root, json_path, _md_path = resolve(root_arg)
    data, problem = read_backlog(json_path)
    if data is None:
        print(problem)
        print("  旧表格格式：由 agent 按 agile-backlog/references/backlog-rules.md §七 一次性转写")
        return 1
    report = collect_backlog_age(data, scan_sprints(root), date.today())
    print("\n".join(render_review_lines(report)))
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

    for name in SIDE_FILES:
        path = root / DOCS_DIR / name
        if not path.exists():
            continue
        payload = load_json(path)
        if payload is None:
            problems.append(f"结构[{name}]：不是合法 JSON")
            continue
        errors, warnings = SIDE_VALIDATORS[name](payload, date.today())
        problems.extend(f"结构[{name}]：" + line for line in errors)
        problems.extend(f"规范[{name}]：" + line for line in warnings)
        if data is not None:
            problems.extend(f"跨文件[{name}]：" + line for line in check_side_refs(root, data, name))

    if md_path.exists():
        # PRODUCT-BACKLOG.md 已随 5.6.0 退役：不再生成、不再比对，只提醒清理。
        print(f"提示：{md_path.name} 已不再生成（遗留产物，确认无自定义内容后可删除）")

    if not problems:
        stats = compute_stats(data)
        print(f"通过：{stats['total']} 条 / {stats['points']} 点，结构 / 对账 / 回填 / Sprint 头 / 小文件全过")
        for line in render_side_lines(root):
            print(line)
        return 0
    print(f"发现 {len(problems)} 处问题：")
    for line in problems:
        print("  · " + line)
    return 1


def cli_trend(root_arg: str | None) -> int:
    """打印已关闭 Sprint 的趋势；只读。"""
    root = Path(root_arg) if root_arg else Path.cwd()
    print("\n".join(render_trend_lines(root)))
    return 0


def cli_report(root_arg: str | None) -> int:
    """一页纸状态（stdout，不落文件）——给汇报/复盘当素材。"""
    root = Path(root_arg) if root_arg else Path.cwd()
    if not (root / DOCS_DIR).is_dir():
        print("没有 agile-docs/：项目未启用敏捷套件。")
        return 1
    print("\n".join(render_report_lines(root)))
    return 0


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
    "review": cli_review,
    "check": cli_check,
    "trend": cli_trend,
    "report": cli_report,
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
