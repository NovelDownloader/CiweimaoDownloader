# Build a self-contained Windows package (source + embedded Python).
# Shortcut for: pwsh package.ps1
& (Join-Path $PSScriptRoot "package.ps1") @args
