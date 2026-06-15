#!/usr/bin/env bash
# CiweimaoDownloader portable launcher
# All dependencies (Python, packages, ADB) are bundled in this directory.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Prepend bundled ADB to PATH
if [ -d "$SCRIPT_DIR/adb" ]; then
    export PATH="$SCRIPT_DIR/adb:$PATH"
fi

exec "$SCRIPT_DIR/python/bin/python3" src/main.py "$@"
