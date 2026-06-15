# Build a self-contained Windows package.
# Bundles: embedded Python 3.11, all pip deps, ADB, source code.
# Output: dist/CiweimaoDownloader-windows-x64.zip
# Host requirements: PowerShell, curl/tar (Windows 10+ built-in)
param(
    [switch]$SkipDownload = $false
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$Dist = "dist\CiweimaoDownloader"
$PythonVersion = "3.11.15"
$PythonBuildDate = "20260610"
$PythonFilename = "cpython-$PythonVersion+$PythonBuildDate-x86_64-pc-windows-msvc-install_only.tar.gz"
$PythonUrl = "https://github.com/astral-sh/python-build-standalone/releases/download/$PythonBuildDate/$PythonFilename"
$PythonCache = "dist\.cache\$PythonFilename"

Write-Host "=== Cleaning dist ==="
if (Test-Path $Dist) { Remove-Item -Recurse -Force $Dist }
Remove-Item "dist\CiweimaoDownloader-windows-x64.zip" -Force -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force -Path $Dist, "dist\.cache" | Out-Null

# ---- Embedded Python ----
Write-Host "=== Downloading embedded Python $PythonVersion ==="
if (-not $SkipDownload) {
    if (Test-Path $PythonCache) {
        Write-Host "Using cached $PythonFilename"
    } else {
        Invoke-WebRequest -Uri $PythonUrl -OutFile $PythonCache
    }
}

Write-Host "=== Extracting Python ==="
New-Item -ItemType Directory -Force -Path "$Dist\python" | Out-Null
tar -xzf $PythonCache -C "$Dist\python" --strip-components=1
if ($LASTEXITCODE -ne 0) { throw "tar extract failed" }

Write-Host "=== Installing Python dependencies ==="
$ReqFile = [System.IO.Path]::GetTempFileName()
try {
    Get-Content requirements.txt | Where-Object { $_ -notmatch '^\s*(#|$)' -and $_ -notmatch 'nuitka' } | Set-Content $ReqFile
    & "$Dist\python\python.exe" -m pip install --no-warn-script-location -r $ReqFile
    if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
} finally {
    Remove-Item $ReqFile -Force -ErrorAction SilentlyContinue
}

# ---- ADB ----
Write-Host "=== Downloading ADB platform-tools ==="
$AdbZip = "dist\.cache\adb-tmp.zip"
if (-not $SkipDownload) {
    Invoke-WebRequest -Uri "https://dl.google.com/android/repository/platform-tools-latest-windows.zip" -OutFile $AdbZip
}

Write-Host "=== Extracting ADB ==="
Add-Type -AssemblyName System.IO.Compression.FileSystem
$Zip = [System.IO.Compression.ZipFile]::OpenRead($AdbZip)
New-Item -ItemType Directory -Force -Path "$Dist\adb" | Out-Null
foreach ($entry in $Zip.Entries) {
    if ($entry.FullName.StartsWith("platform-tools/") -and -not $entry.FullName.EndsWith("/")) {
        $target = Join-Path "$Dist\adb" (Split-Path -Leaf $entry.FullName)
        [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $target, $true)
    }
}
$Zip.Dispose()
Remove-Item $AdbZip -Force -ErrorAction SilentlyContinue

# ---- Source & config ----
Write-Host "=== Copying source files ==="
Copy-Item -Recurse src "$Dist\"
Get-ChildItem -Recurse -Directory -Path "$Dist\src" -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Path "$Dist\src" -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force
Copy-Item setting.yaml "$Dist\"
Copy-Item run.bat "$Dist\"

# ---- Package ----
Write-Host "=== Packaging ==="
$ZipOut = "dist\CiweimaoDownloader-windows-x64.zip"
Compress-Archive -Path "$Dist\*" -DestinationPath $ZipOut -Force

Write-Host "=== Done ==="
$ZipFile = Get-Item $ZipOut
Write-Host "Output: $($ZipFile.FullName) ($([math]::Round($ZipFile.Length / 1MB, 1)) MB)"
