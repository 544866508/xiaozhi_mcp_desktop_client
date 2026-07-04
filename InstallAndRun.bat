@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ====================== Config Area ======================
set TARGET_PY_VER=3.14
set PY_INSTALL_PATH=D:\Program Files\Python\Python314
set VENV_NAME=mcp_mini_venv
set ALIYUN_PIP=https://mirrors.aliyun.com/pypi/simple/
set PY_FULL_EXE=%PY_INSTALL_PATH%\python.exe
set INSTALLER_NAME=python-3.14.5-amd64.exe
set PKG_DIR=pkg
:: =======================================================

echo ==============================================
echo MCP Auto Deployment Script
echo Required Python %TARGET_PY_VER%, other versions will be reinstalled automatically
echo Python Install Path: %PY_INSTALL_PATH%
echo Installer Filename: %INSTALLER_NAME%
echo Virtual Env Directory: %~dp0%VENV_NAME%
echo ==============================================
echo.
cd /d "%~dp0"

:: Auto create pkg folder if not exists, place installer here
md "%PKG_DIR%" 2>nul
:: Full installer path: script root/pkg/installer.exe
set INSTALLER=%~dp0%PKG_DIR%\%INSTALLER_NAME%

set NEED_INSTALL=1
set PY_RUN=

echo [1] Detect current python -V version
python -V >tmp_ver.txt 2>&1
type tmp_ver.txt
findstr /C:"Python %TARGET_PY_VER%" tmp_ver.txt >nul 2>&1
if !errorlevel! equ 0 (
    echo Current Python version matches %TARGET_PY_VER%, skip installation
    set PY_RUN=python
    set NEED_INSTALL=0
)
del tmp_ver.txt

if !NEED_INSTALL! equ 1 (
    echo Current Python version is not %TARGET_PY_VER%, start silent install of 3.14.5
    if not exist "%INSTALLER%" (
        echo [Fatal Error] Missing installer file %INSTALLER_NAME% in current directory
        echo Full search path: "%INSTALLER%"
        pause
        exit /b 1
    )

    md "%PY_INSTALL_PATH%" 2>nul
    echo Directory created: %PY_INSTALL_PATH%
    echo Installing Python, please wait...

    :: All parameters in one line to avoid popup caused by line break caret
    "%INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_doc=0 Include_launcher=1 TargetDir="%PY_INSTALL_PATH%"

    echo Waiting for installation write completion, delay 15 seconds...
    timeout /t 15 /nobreak >nul

    if not exist "%PY_FULL_EXE%" (
        echo.
        echo ##################################################
        echo Python installation failed! Path: "%PY_FULL_EXE%"

        echo Please troubleshoot following items step by step:

        echo 1. First run requires admin rights for Python install and venv creation; normal double-click works afterwards

        echo 2. Temporarily disable anti-virus software

        echo 3. Check if target disk has write permission

        echo ##################################################
        pause
        exit /b 2
    )
    echo Python 3.14 installed successfully
    set PY_RUN="%PY_FULL_EXE%"
)

:PY_OK
echo.
echo [2] Check virtual environment %VENV_NAME%
set VENV_DIR=%~dp0%VENV_NAME%
set VENV_ACT=%VENV_DIR%\Scripts\activate.bat


if exist "%VENV_ACT%" (
    echo Virtual environment exists, skip creation and launch program directly
    goto RUN_PROG
)

echo Virtual env not found, creating new %VENV_NAME%
%PY_RUN% -m venv %VENV_NAME%

call "%VENV_ACT%"
echo.
echo [3] Upgrade pip and install dependencies (Alibaba Mirror)
if exist "requirements.txt" (
    python -m pip install --upgrade pip -i %ALIYUN_PIP% --trusted-host mirrors.aliyun.com
    python -m pip install -r requirements.txt -i %ALIYUN_PIP% --trusted-host mirrors.aliyun.com
) else (
    echo requirements.txt not found, skip dependency installation
)

:RUN_PROG
echo Activate virtual environment
call "%VENV_ACT%"
echo.
echo [4] Launch mcp_client.py
if not exist "mcp_client.py" (
    echo Error: mcp_client.py not found
    pause
    exit /b 3
)
echo ==============================================
python mcp_client.py
echo ==============================================
echo Program exited, press any key to close window
pause >nul
deactivate
endlocal