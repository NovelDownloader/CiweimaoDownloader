#!/bin/bash
# Nuitka 打包脚本 (Linux 版)

set -e  # 遇到错误立即退出

# ---------- 1. 安装编译必要的系统组件 ----------
echo ">>> 检查并安装编译依赖 (gcc, python3-dev) ..."
if command -v apt-get &> /dev/null && command -v sudo &> /dev/null; then
    # 检测是否已安装（可选，但直接安装幂等）
    sudo apt-get update
    sudo apt-get install -y gcc python3-dev
    echo "依赖安装完成。"
else
    echo "⚠️ 警告: 未检测到 apt-get 或 sudo，请手动确保 gcc 和 python3-dev 已安装。"
fi

# ---------- 2. 检查 Nuitka ----------
if ! python3 -m nuitka --version &> /dev/null; then
    echo "❌ 错误: 未找到 Nuitka，请先安装: pip install nuitka"
    exit 1
fi

# ---------- 3. 执行打包 ----------
echo ">>> 开始 Nuitka 打包 ..."
python3 -m nuitka --onefile \
    --output-dir=build \
    --include-data-files=./setting.yaml=setting.yaml \
    --jobs=8 \
    --quiet \
    ./src/main.py

# ---------- 4. 检查结果 ----------
if [ $? -eq 0 ]; then
    echo "✅ 打包成功！可执行文件位于 build/main.bin (或 build/main)"
else
    echo "❌ 打包失败，请检查错误信息。"
    exit 1
fi