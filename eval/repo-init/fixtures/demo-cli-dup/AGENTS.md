# AGENTS.md

## Project overview

demo-cli 是一个 Python CLI 工具，从 CSV 输入文件生成汇总报表。技术栈：Python 3.10+、pip。

## Setup commands

- Install: `pip install -e .`
- Run: `python -m demo_cli.main --input data.csv --output report.txt`
- Test: `pytest -v`（注意：全量测试用 -v 输出）

## Code style

- 模块 docstring 必须存在
- 命令行参数用 argparse

## Hard constraints

- 不允许直接改 `src/demo_cli/main.py` 的 summarize 函数签名
- 输入 CSV 必须是 UTF-8

## Known gotchas

- CSV 非 UTF-8 会报 UnicodeDecodeError
