@echo off
chcp 65001 >nul
cd /d "%~dp0"
title DickOnTop 本地服务器

if not exist "index.html" (
  echo [错误] 没有找到 index.html。
  echo 请先把整个压缩包完整解压，再运行 serve.bat。
  echo.
  pause
  exit /b 1
)

if not exist "serve.py" (
  echo [错误] 没有找到 serve.py，请重新解压完整的网页版压缩包。
  echo.
  pause
  exit /b 1
)

set "PY="

rem 优先用 py 启动器，它能绕开 Windows 应用商店的 python 假别名
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -c "import sys" >nul 2>nul
  if not errorlevel 1 set "PY=py -3"
)

if not defined PY (
  where python >nul 2>nul
  if not errorlevel 1 (
    python -c "import sys" >nul 2>nul
    if not errorlevel 1 set "PY=python"
  )
)

if not defined PY (
  echo [错误] 没有找到可用的 Python 3。
  echo.
  echo 请先安装 Python 3：https://www.python.org/downloads/
  echo 安装时勾选 "Add python.exe to PATH"，装完重新双击 serve.bat。
  echo.
  pause
  exit /b 1
)

set "PYTHONIOENCODING=utf-8"
%PY% serve.py
if errorlevel 1 (
  echo.
  echo 服务器异常退出，请把上面的提示截图反馈。
  pause
)
