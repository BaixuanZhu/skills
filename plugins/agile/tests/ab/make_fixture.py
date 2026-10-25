"""AB 实验 fixture 生成：保证各组的文件完全一致，唯一差异是注入文本。

每步都校验，任何一个目录文件清单不同就直接报错，不让不一致的 fixture 进入测试。
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

# 从自身位置推导：tests/ab/ → stage fixtures 与插件脚本，产物写临时目录（启动时打印）
HERE = pathlib.Path(__file__).resolve()
TESTS = HERE.parent.parent          # plugins/agile/tests
SRC = TESTS / "stage"
AGILE = TESTS.parent / "scripts" / "agile.py"
OUT = pathlib.Path(tempfile.mkdtemp(prefix="agile-ab-"))

GROUPS = {
    "sprint": ["s1a", "s1b"],
    "active": ["s2a", "s2b"],
}

# 第二轮复验用同名加后缀，便于逐轮对照
if len(sys.argv) > 1 and sys.argv[1] == "r2":
    GROUPS = {k: [n + "2" for n in v] for k, v in GROUPS.items()}

# 第三轮：只验修完文案后的 active 场景
if len(sys.argv) > 1 and sys.argv[1] == "r3":
    GROUPS = {"active": ["s2b3", "s2b4"]}


def build(stage: str, name: str) -> None:
    dst = OUT / name
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    shutil.copytree(SRC / stage / "agile-docs", dst / "agile-docs")
    if (SRC / stage / "sprints").is_dir():
        shutil.copytree(SRC / stage / "sprints", dst / "sprints")

    # 第一阶段全部确认：否则 sprint 场景无一条可取，容量问题被遮蔽
    p = dst / "agile-docs" / "backlog.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    for item in data["phases"][0]["items"]:
        item["confirmed"] = True
        if item.get("priority") == "Could":
            item["priority"] = "Should"
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 渲染：让所有组都有 PRODUCT-BACKLOG.md，指纹与 json 一致
    r = subprocess.run(
        [sys.executable, str(AGILE), "render", str(dst)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise SystemExit(f"render 失败 {name}: {r.stderr}")


def fingerprint_check(name: str) -> None:
    import hashlib
    import re
    root = OUT / name
    data = json.loads((root / "agile-docs" / "backlog.json").read_text(encoding="utf-8"))
    fp = hashlib.sha256(
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:16]
    md = (root / "agile-docs" / "PRODUCT-BACKLOG.md").read_text(encoding="utf-8")
    m = re.search(r"backlog-sha256:\s*([0-9a-f]+)", md)
    if not m or m.group(1) != fp:
        raise SystemExit(f"{name}: md 指纹不一致")


def manifest(name: str) -> list[str]:
    root = OUT / name
    return sorted(
        str(p.relative_to(root)).replace("\\", "/")
        for p in root.rglob("*") if p.is_file()
    )


def main() -> None:
    print(f"fixture 输出目录：{OUT}")
    all_names = []
    for stage, names in GROUPS.items():
        for n in names:
            build(stage, n)
            all_names.append(n)

    for n in all_names:
        fingerprint_check(n)

    # 只在同一场景内比较：两个场景本来就该有不同的初始文件
    for stage, names in GROUPS.items():
        ref = manifest(names[0])
        for n in names[1:]:
            other = manifest(n)
            if other != ref:
                raise SystemExit(
                    f"[{stage}] 文件清单不一致 {n}:\n  多 {set(other)-set(ref)}\n  少 {set(ref)-set(other)}"
                )
        print(f"[{stage}] {len(names)} 组一致，{len(ref)} 个文件")
        for f in ref:
            print("   ", f)


if __name__ == "__main__":
    main()
