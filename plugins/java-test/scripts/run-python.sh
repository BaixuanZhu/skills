#!/bin/sh
# 插件 hook 的 Python 入口：兼容 python / python3 / py，并用 exec 原样传退出码。
# 解释器或脚本参数缺失时静默退出，不干扰用户主流程。

here=$(dirname "$0")
script=${1:-}
[ -n "$script" ] || exit 0
shift

for py in python python3 py; do
  if command -v "$py" >/dev/null 2>&1; then
    exec "$py" "$here/$script" "$@"
  fi
done

exit 0
