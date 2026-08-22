# CLAUDE.md

## 项目概述

demo-cli 是一个 Python CLI 工具，从 CSV 输入文件生成汇总报表。Python 3.10+，pip 安装。

## 常用命令

- 安装：`pip install -e .`
- 运行：`python -m demo_cli.main --input data.csv --output report.txt`
- 测试：`pytest`

## 代码规范

- 模块 docstring 必须存在
- 命令行参数用 argparse，不用 click

## 注意事项

- 输入 CSV 的编码必须是 UTF-8，否则会报 UnicodeDecodeError
- 不允许直接改 `src/demo_cli/main.py` 的 summarize 函数签名
