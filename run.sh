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

# Run Python (disable 'set -e' temporarily so we can pause even on error)
set +e
"$SCRIPT_DIR/python/bin/python3" src/main.py "$@"
EXIT_CODE=$?
set -e

# Pause to allow reading output before the window closes
echo ""
echo "按任意键继续..."
read -n 1 -s -r -p "" || true

exit $EXIT_CODE