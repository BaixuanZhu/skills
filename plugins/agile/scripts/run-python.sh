#!/bin/sh
# hook 的解释器入口。
#
# 为什么需要这一层：hooks.json 用 exec form 直连解释器，但 `python` 在
# macOS / 部分 Linux 上不存在（只有 python3）。这里依次探测，找到就 exec
# （exec 保证 exit code 原样传出，exit 2 的语义不会被吞）。
#
# fail-open：一个都没有时安静退出 0。门禁装不上，不能让用户的每次编辑都报错。

here=$(dirname "$0")

for py in python python3 py; do
  if command -v "$py" >/dev/null 2>&1; then
    exec "$py" "$here/agile.py" "$@"
  fi
done

exit 0
