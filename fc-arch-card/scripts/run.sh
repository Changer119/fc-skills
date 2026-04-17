#!/bin/bash
# fc-arch-card 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 切换到项目目录
cd "$PROJECT_DIR"

# 检查依赖
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed"
    exit 1
fi

# 安装依赖（如果未安装）
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# 安装依赖
uv pip install -r requirements.txt -q

# 安装 Playwright chromium（如果未安装）
if ! uv run python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(headless=True); p.stop()" 2>/dev/null; then
    echo "Installing Playwright chromium browser..."
    uv run playwright install chromium
fi

# 运行主程序
uv run python -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
from assets.capture import capture_diagram
from assets.render_server import start_server

print('fc-arch-card dependencies ready')
print('Use: uv run python assets/capture.py --url <url> --output <png>')
"
