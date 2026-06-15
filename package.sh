#!/usr/bin/env bash
# Build a self-contained Linux package.
# Bundles: embedded Python 3.11, all pip deps, ADB, source code.
# Output: dist/CiweimaoDownloader-linux-x64.tar.gz
# Host requirements: curl, python3 (for build-time zipfile extraction only)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

DIST="dist/CiweimaoDownloader"
PYTHON_FILENAME="cpython-3.11.15+20260610-x86_64-unknown-linux-gnu-install_only.tar.gz"
PYTHON_URL="https://github.com/astral-sh/python-build-standalone/releases/download/20260610/${PYTHON_FILENAME}"
PYTHON_CACHE="dist/.cache/${PYTHON_FILENAME}"

echo "=== Cleaning dist ==="
rm -rf "$DIST" dist/CiweimaoDownloader-*.tar.gz

mkdir -p "$DIST" "dist/.cache"

# ---- Embedded Python ----
echo "=== Downloading embedded Python 3.11 ==="
if [ -f "$PYTHON_CACHE" ]; then
    echo "Using cached ${PYTHON_FILENAME}"
else
    curl -sL "$PYTHON_URL" -o "$PYTHON_CACHE"
fi

echo "=== Extracting Python ==="
mkdir -p "$DIST/python"
tar -xzf "$PYTHON_CACHE" -C "$DIST/python" --strip-components=1

echo "=== Installing Python dependencies ==="
sed '/^#/d; /^$/d; /nuitka/d' requirements.txt | "$DIST/python/bin/python3" -m pip install --no-warn-script-location -r /dev/stdin

# ---- ADB ----
echo "=== Downloading ADB platform-tools ==="
ADB_ZIP="dist/.cache/adb-tmp.zip"
curl -sL "https://dl.google.com/android/repository/platform-tools-latest-linux.zip" -o "$ADB_ZIP"
mkdir -p "$DIST/adb"
python3 -c "
import zipfile
with zipfile.ZipFile('$ADB_ZIP') as z:
    for f in z.namelist():
        if f.startswith('platform-tools/') and not f.endswith('/'):
            z.extract(f, '$DIST/adb')
"
# Flatten: move files from platform-tools/ up to adb/
mv "$DIST/adb/platform-tools/"* "$DIST/adb/" 2>/dev/null || true
rmdir "$DIST/adb/platform-tools" 2>/dev/null || true
chmod +x "$DIST/adb/"*
rm -f "$ADB_ZIP"

# ---- Source & config ----
echo "=== Copying source files ==="
cp -r src "$DIST/"
find "$DIST/src" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$DIST/src" -name '*.pyc' -delete 2>/dev/null || true
cp setting.yaml "$DIST/"
cp run.sh "$DIST/"
chmod +x "$DIST/run.sh"

# Remove stale done markers so re-runs work
find "$DIST/data" -name done -delete 2>/dev/null || true

# ---- Package ----
echo "=== Packaging ==="
tar -czf "dist/CiweimaoDownloader-linux-x64.tar.gz" -C dist CiweimaoDownloader

echo "=== Done ==="
ls -lh "dist/CiweimaoDownloader-linux-x64.tar.gz"
echo ""
echo "Test: tar -xzf dist/CiweimaoDownloader-linux-x64.tar.gz -C /tmp && /tmp/CiweimaoDownloader/run.sh"
