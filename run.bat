@echo off
set "SCRIPT_DIR=%~dp0"
set "PATH=%SCRIPT_DIR%adb;%PATH%"
"%SCRIPT_DIR%python\python.exe" "%SCRIPT_DIR%src\main.py" %*
