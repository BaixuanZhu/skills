"""demo-cli: 从 CSV 生成汇总报表。"""

import argparse
import csv
import sys


def summarize(rows):
    total = sum(float(r["amount"]) for r in rows)
    count = len(rows)
    return {"count": count, "total": total}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="demo-cli")
    parser.add_argument("--input", required=True, help="CSV 输入文件")
    parser.add_argument("--output", required=True, help="报表输出路径")
    args = parser.parse_args(argv)

    with open(args.input, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    result = summarize(rows)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(f"count={result['count']}\n")
        f.write(f"total={result['total']:.2f}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
