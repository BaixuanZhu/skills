#!/usr/bin/env python3
"""java-test 达尔文评估：对 A-D 四组生成测试跑固定 mutation 清单。"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "fixture"
RUNS = ROOT / "runs"
SOURCE_REL = Path("src/main/java/com/example/eval/PricingService.java")

MUTANTS = {
    "M1-discount-off": (
        "        if (total.compareTo(DISCOUNT_THRESHOLD) >= 0) {",
        "        if (false) {",
    ),
    "M2-invalid-quantity-returns-zero": (
        '            throw new IllegalArgumentException("quantity must be positive");',
        "            return BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP);",
    ),
    "M3-scale-zero": (
        "        return total.setScale(2, RoundingMode.HALF_UP);",
        "        return total.setScale(0, RoundingMode.HALF_UP);",
    ),
    "M4-round-down": (
        "        return amount.divide(BigDecimal.valueOf(people), 2, RoundingMode.HALF_UP);",
        "        return amount.divide(BigDecimal.valueOf(people), 2, RoundingMode.DOWN);",
    ),
}


def run_tests(project):
    mvn = shutil.which("mvn.cmd") or shutil.which("mvn")
    if not mvn:
        raise RuntimeError("Maven executable not found")
    result = subprocess.run(
        [mvn, "-q", "test"],
        cwd=project,
        text=True,
        capture_output=True,
    )
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def mutate(source_text, old, new):
    if old not in source_text:
        raise RuntimeError(f"mutation source not found: {old!r}")
    return source_text.replace(old, new, 1)


def evaluate_group(group):
    run_dir = RUNS / group
    source = (run_dir / SOURCE_REL).read_text(encoding="utf-8")
    report = {"group": group, "baseline": None, "mutants": {}}

    with tempfile.TemporaryDirectory(prefix=f"java-test-mutant-{group}-") as temp:
        temp_root = Path(temp)
        baseline = temp_root / "baseline"
        shutil.copytree(run_dir, baseline)
        code, output = run_tests(baseline)
        report["baseline"] = {
            "exit_code": code,
            "passed": code == 0,
            "tail": output[-1000:],
        }

        for name, (old, new) in MUTANTS.items():
            mutant = temp_root / name
            shutil.copytree(run_dir, mutant)
            mutated = mutate(source, old, new)
            (mutant / SOURCE_REL).write_text(mutated, encoding="utf-8")
            code, output = run_tests(mutant)
            report["mutants"][name] = {
                "exit_code": code,
                "killed": code != 0,
                "tail": output[-1000:],
            }

    killed = sum(1 for item in report["mutants"].values() if item["killed"])
    report["killed_count"] = killed
    report["mutation_score"] = killed / len(MUTANTS)
    return report


def main():
    reports = [evaluate_group(group) for group in ("A", "B", "C", "D")]
    (ROOT / "mutation-results.json").write_text(
        json.dumps(reports, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = ["# Mutation 检出结果", ""]
    lines.append("| 组 | baseline | M1 | M2 | M3 | M4 | 杀死数 | 分数 |")
    lines.append("|---|---|---|---|---|---|---:|---:|")
    for report in reports:
        row = [report["group"], "PASS" if report["baseline"]["passed"] else "FAIL"]
        for name in MUTANTS:
            row.append("KILLED" if report["mutants"][name]["killed"] else "SURVIVED")
        row.extend([str(report["killed_count"]), f"{report['mutation_score']:.0%}"])
        lines.append("| " + " | ".join(row) + " |")
    (ROOT / "mutation-results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
