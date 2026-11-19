#!/usr/bin/env python3
"""PostToolUse hook：构建失败后按已知症状注入 MyBatis-Plus 排查指针。

只在真实使用 MyBatis-Plus 的项目中激活；不诊断、不改代码、不阻断操作。
状态与门控缓存位于系统临时目录；任何异常都静默退出。
"""

import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time

LOG = ".mvn-logs/build.log"
STALE_MS = 10 * 60 * 1000
GATE_TTL_MS = 60 * 60 * 1000
MAX_SCAN = 512 * 1024

SYMPTOMS = [
    {
        "token": "Invalid bound statement",
        "hint": (
            "三步排查，按命中率排序：① 接口方法与 XML 的 id 是否同名同参 "
            "② mapper-locations 能否命中该 XML ③ @MapperScan 包路径是否覆盖该 Mapper。"
            "只写接口不写 XML（或反之）必然报这个。"
        ),
    },
    {
        "token": "BindingException",
        "hint": '多参方法缺 @Param：每个参数加 @Param("x")，XML 里用 #{x}。注意报错里列出的 arg0/param1 不是真实参数名。',
    },
    {
        "token": "Duplicate entry",
        "also": "for key",
        "hint": (
            "MySQL 唯一约束冲突。若该表启用了逻辑删除：唯一索引必须包含删除标记列"
            "（如 UNIQUE(username, deleted)），否则删过的值再也插不进去。"
        ),
    },
    {
        "token": "duplicate key value violates unique constraint",
        "hint": "PostgreSQL 唯一约束冲突。若该表启用了逻辑删除：唯一索引必须包含删除标记列，否则删过的值再也插不进去。",
    },
    {
        "token": "Unknown column",
        "hint": (
            'MySQL 字段名对不上。先查 Wrapper 里有没有字符串形式的字段名（eq("user_name", …)——'
            "改名后不报错，只查错数据），再查驼峰配置与 @TableField。"
        ),
    },
    {
        "token": "does not exist",
        "also": 'column "',
        "hint": (
            'PostgreSQL 字段名对不上。先查 Wrapper 里有没有字符串形式的字段名（eq("user_name", …)），'
            "再查驼峰配置与 @TableField。"
        ),
    },
]

POINTER = "详见技能 mybatis-plus-dev 的 references/09-troubleshoot.md §2（常见异常定位）"
BUILD_COMMAND = re.compile(r"(^|[\s;&|])(\./)?(mvn|mvnw|gradle|gradlew)(\s|$)")
MP_MARKER = re.compile(r"mybatis-?plus", re.IGNORECASE)


def now_ms():
    return int(time.time() * 1000)


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
        pass


def project_has_mp(root, cache_path):
    """构建依赖、既有约定文件或源码标记任一命中即激活。"""
    cached = read_json(cache_path, None)
    if isinstance(cached, dict):
        if cached.get("v") is True:
            return True
        if cached.get("v") is False and now_ms() - cached.get("ts", 0) < GATE_TTL_MS:
            return False

    has = False
    for marker in ("pom.xml", "build.gradle", "build.gradle.kts"):
        path = Path(root) / marker
        try:
            if path.stat().st_size > MAX_SCAN:
                continue
            if MP_MARKER.search(path.read_text(encoding="utf-8", errors="replace")):
                has = True
                break
        except OSError:
            pass

    if not has:
        for seed in (".claude/rules/mybatis-plus.md", "CLAUDE.md"):
            try:
                if MP_MARKER.search((Path(root) / seed).read_text(encoding="utf-8", errors="replace")):
                    has = True
                    break
            except OSError:
                pass

    write_json(cache_path, {"v": has, "ts": now_ms()})
    return has


def response_text(response):
    if isinstance(response, str):
        return response
    if not isinstance(response, dict):
        return ""
    return "\n".join(
        str(response[key])
        for key in ("stdout", "stderr", "output", "content")
        if response.get(key)
    )


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (ValueError, UnicodeError):
        return
    if not isinstance(payload, dict):
        return

    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    if not isinstance(tool_input, dict):
        return
    if not BUILD_COMMAND.search(str(tool_input.get("command") or "")):
        return

    root = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    root_hash = hashlib.md5(str(root).encode("utf-8")).hexdigest()[:12]
    state_dir = Path(tempfile.gettempdir()) / "claude-symptom"
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    if not project_has_mp(root, state_dir / f"{root_hash}.gate.json"):
        return

    text = ""
    log_path = Path(root) / LOG
    try:
        if now_ms() - log_path.stat().st_mtime * 1000 <= STALE_MS:
            text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        pass

    response = payload.get("tool_response") or payload.get("toolResponse")
    if response:
        text += "\n" + response_text(response)
    if not text.strip():
        return

    state_path = state_dir / f"{root_hash}.json"
    state = read_json(state_path, {})
    if not isinstance(state, dict):
        state = {}
    session_id = str(payload.get("session_id") or payload.get("sessionId") or "no-session")
    session_state = state.get(session_id) or {}
    reported_list = session_state.get("tokens", []) if isinstance(session_state, dict) else []
    reported = set(reported_list)

    present = [
        symptom["token"]
        for symptom in SYMPTOMS
        if symptom["token"] in text and (not symptom.get("also") or symptom["also"] in text)
    ]
    kept = [token for token in reported_list if token in present]
    hit = next(
        (symptom for symptom in SYMPTOMS if symptom["token"] in present and symptom["token"] not in reported),
        None,
    )

    if len(kept) != len(reported) or hit:
        tokens = list(dict.fromkeys(kept + present)) if hit else kept
        state[session_id] = {"tokens": tokens, "ts": now_ms()}
        write_json(state_path, state)

    if not hit:
        return

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": f'构建日志命中「{hit["token"]}」→ {hit["hint"]}\n{POINTER}',
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
