#!/usr/bin/env bash
# 激活仓库的 git hooks（pre-push 等）。
#
# 用法（在仓库根目录）：
#   bash scripts/install-hooks.sh
#   # 或
#   ./scripts/install-hooks.sh

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if [ ! -d ".githooks" ]; then
    echo "❌ 找不到 .githooks/ 目录"
    exit 1
fi

# 设置 hooks 路径到 .githooks（仓库本地，不会污染全局）
git config core.hooksPath .githooks

# 确保所有 hook 可执行
find .githooks -type f -exec chmod +x {} +

echo "✅ hooks 已激活（path = .githooks）"
echo ""
echo "已注册的 hook："
ls -la .githooks/
echo ""
echo "提示：clone 完本仓库后只需运行一次本脚本。"