#!/bin/bash
# Nuitka 打包脚本 (Linux 版)

# 检查 Nuitka 是否安装
if ! python3 -m nuitka --version &> /dev/null; then
    echo "错误: 未找到 Nuitka，请先安装: pip install nuitka"
    exit 1
fi

# 执行打包命令
python3 -m nuitka --onefile \
    --output-dir=build \
    --include-data-files=./setting.yaml=setting.yaml \
    --jobs=8 \
    --verbose \
    ./src/main.py

# 检查打包是否成功
if [ $? -eq 0 ]; then
    echo "打包成功！可执行文件位于 build/main.bin (或 build/main)"
else
    echo "打包失败，请检查错误信息。"
    exit 1
fi