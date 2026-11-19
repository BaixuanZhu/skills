#!/usr/bin/env python3
"""PostToolUse hook：按测试类型注入短判据，负责召回完整技能与交付闭环。

单测与集成测试按文件名分流：生成细节不塞进摘要，只给技能路径与关键判据。
只读取工具传入的路径元数据，不解析测试代码、不诊断、不改文件、不阻断操作。
Claude Code / ZCode 从 file_path 取路径；Codex apply_patch 从 patch 声明行取路径。
状态放在系统临时目录；任何异常都静默退出，避免 hook 自身干扰主流程。
"""

import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time

REARM_MS = 60 * 1000

PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def skill_path(skill_name):
    return str(PLUGIN_ROOT / "skills" / skill_name / "SKILL.md")


def criteria_for(kind):
    """短注入只负责路由与交付闭环；完整判据仍在随插件分发的技能正文。"""
    if kind == "integration":
        return "\n".join(
            [
                "[java-test:integration] 刚写入/改动集成测试文件；本摘要不是完整规范。",
                f"① 加载：若当前上下文没有技能正文，先读取「{skill_path('java-integration-test')}」；命中假绿症状再读同目录 references/01-pitfalls.md。",
                "② 继续条件：只有用户明示「补集成测试 / 需求冻结 / 发版」才直接开始；仅提到真实依赖行为（唯一约束、事务回滚等）属推断，先确认后再扩展新集成用例；存量用例照跑照修。",
                "③ 决策：按「建不建 → 放哪层 → 用什么跑」核对；应用层 exists/前置检查不替代 DB 约束；检查生产路径、断言时间点、失败是否真会判红；每特性 1~3 条，不铺分支矩阵。",
                "④ 环境与执行：声明 Docker / 实库 / 替身路径及盲区；实际运行 mvn verify / ./gradlew check（或项目既有集成任务），从输出/报告确认本次 *IT 被执行；用结构化断言，不靠 curl / 肉眼。",
                "⑤ 反证：至少一条关键断言做「改坏实现 → 目标测试变红 → 恢复后重跑变绿」；无法执行或反证必须明确披露。",
            ]
        )
    return "\n".join(
        [
            "[java-test:unit] 刚写入/改动单测文件；本摘要不是完整规范。",
            f"① 加载：若当前上下文没有技能正文，先读取「{skill_path('java-unit-test')}」；命中假绿症状再读同目录 references/01-pitfalls.md。涉及真实依赖、@SpringBootTest 或切片注解时改用 java-integration-test。",
            "② 设计：设计先于编码，清单先行（对刚写入的用例逐项复核补缺，后续生成同此标准）——四维各至少一条（正向/反向/边界/异常）；有业务组合规则才画决策表、列数即用例数，条件相互独立不展开全排列；3~8 条是常态，超出先防凑数；同区间换代表值行为应不变。",
            "③ 质量：mock 必须是被测代码真正使用的实例；副作用必须 verify（或假对象状态断言）；断言必须可能失败（具体异常、金额比较口径、无恒真/空断言）；时间/随机注入（Clock/固定种子），禁 Thread.sleep 与执行顺序依赖。",
            "④ 执行：实际运行 mvn test / ./gradlew test（或项目既有单测任务），从输出/报告确认本次用例被执行；BUILD SUCCESS 不是执行证据。",
            "⑤ 反证：至少一条核心断言做「改坏实现 → 目标测试变红 → 恢复后重跑变绿」；只设计区分性用例或验证 BigDecimal 语义不算反证；无法执行或反证必须明确披露。",
        ]
    )

PATCH_FILE_LINE = re.compile(
    r"^\*\*\*\s*(?:Update|Add|Delete)\s+File:\s*(.+?)\s*$", re.MULTILINE
)
PATCH_MOVE_LINE = re.compile(r"^\*\*\*\s*Move\s+to:\s*(.+?)\s*$", re.MULTILINE)


def classify_test_file(path):
    """按文件名识别测试类并分流；不读取测试代码，避免用摘要猜实现。"""
    base = re.split(r"[/\\]", str(path))[-1]
    if not base.endswith(".java"):
        return None
    if re.search(r".+ITCase\.java$", base) or re.search(r"[a-z0-9]IT\.java$", base):
        return "integration"
    if any(
        (
            re.search(r".+Test\.java$", base),
            re.search(r".+Tests\.java$", base),
            re.search(r".+TestCase\.java$", base),
            re.match(r"Test[A-Z].*\.java$", base),
        )
    ):
        return "unit"
    return None


def collect_paths(tool_input):
    """跨产品收集被写入的路径，不扫描 new_string/content 等文件内容。"""
    if not isinstance(tool_input, dict):
        return []
    paths = []
    for key in ("file_path", "filePath", "path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            paths.append(value.strip())
    for key in ("command", "patch", "input"):
        text = tool_input.get(key)
        if not isinstance(text, str) or "***" not in text:
            continue
        for pattern in (PATCH_FILE_LINE, PATCH_MOVE_LINE):
            paths.extend(match.group(1).strip() for match in pattern.finditer(text))
    return paths


def read_json(path, fallback):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, TypeError):
        return fallback


def write_json(path, value):
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False)
    except OSError:
        # 缓存写不进去时宁可重复注入，也不能影响主流程。
        pass


def should_inject(state_path, session_id, dedup_key):
    state = read_json(state_path, {})
    if not isinstance(state, dict):
        state = {}
    now = int(time.time() * 1000)
    seen = state.get(session_id) or {}
    if not isinstance(seen, dict):
        seen = {}
    last = seen.get(dedup_key)
    if isinstance(last, (int, float)) and now - last < REARM_MS:
        return False
    seen[dedup_key] = now
    state[session_id] = seen
    write_json(state_path, state)
    return True


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (ValueError, UnicodeError):
        return
    if not isinstance(payload, dict):
        return

    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    hits = []
    kinds = set()
    for path in collect_paths(tool_input):
        kind = classify_test_file(path)
        if kind:
            hits.append(path)
            kinds.add(kind)
    if not hits:
        return

    root = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    root_hash = hashlib.md5(str(root).encode("utf-8")).hexdigest()[:12]
    state_dir = Path(tempfile.gettempdir()) / "claude-java-test"
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return

    session_id = str(payload.get("session_id") or payload.get("sessionId") or "no-session")
    dedup_key = "|".join(sorted(set(hits)))
    if not should_inject(state_dir / f"{root_hash}.json", session_id, dedup_key):
        return

    criteria = "\n\n".join(
        criteria_for(kind) for kind in ("unit", "integration") if kind in kinds
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": criteria,
                }
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # fail-open：hook 自身出错绝不能干扰正常工作流。
        pass
