# AGENTS.md

## Project overview

demo-cli 是一个 Python CLI 工具，从 CSV 输入文件生成汇总报表。技术栈：Python 3.10+、pip。

## Setup commands

- Install: `pip install -e .`
- Run: `python -m demo_cli.main --input data.csv --output report.txt`
- Test: `pytest`

## Code style

- 模块 docstring 必须存在

## Hard constraints

- 不允许直接改 `src/demo_cli/main.py` 的 summarize 函数签名
