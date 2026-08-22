# demo-cli

一个 Python CLI 工具，从 CSV 文件生成汇总报表。

- 语言：Python 3.10+
- 包管理：pip
- 入口：`python -m demo_cli.main`
- 测试：pytest

## 安装

```bash
pip install -e .
```

## 使用

```bash
python -m demo_cli.main --input data.csv --output report.txt
```

## 测试

```bash
pytest
```
