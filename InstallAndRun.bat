@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ====================== Config Area ======================
set TARGET_PY_VER=3.14
set BASE_PY_FOLDER=\Program Files\Python\Python314
set VENV_NAME=mcp_mini_venv
set ALIYUN_PIP=https://mirrors.aliyun.com/pypi/simple/
set INSTALLER_NAME=python-3.14.5-amd64.exe
set PKG_DIR=pkg
:: =======================================================

:: Auto select install drive: D>E>F>G>H, fallback to C if none available
set DRIVE_LIST=D E F G H
set PY_BASE_DRIVE=C
for %%d in (%DRIVE_LIST%) do (
    if exist %%d:\ (
        set PY_BASE_DRIVE=%%d
        goto DRIVE_FOUND
    )
)
:DRIVE_FOUND
set PY_INSTALL_PATH=!PY_BASE_DRIVE!:!BASE_PY_FOLDER!
set PY_FULL_EXE=!PY_INSTALL_PATH!\python.exe

echo ==============================================
echo MCP Auto Deployment Script
echo Required Python %TARGET_PY_VER%, mismatched versions will trigger reinstall
echo Python Auto Install Drive: !PY_BASE_DRIVE!:
echo Python Install Path: !PY_INSTALL_PATH!
echo Installer Filename: %INSTALLER_NAME%
echo Virtual Env Directory: %~dp0%VENV_NAME%
echo ==============================================
echo.
cd /d "%~dp0"

:: Create pkg folder if missing, place installer here
md "%PKG_DIR%" 2>nul
:: Full installer path: script root/pkg/installer.exe
set INSTALLER=%~dp0%PKG_DIR%\%INSTALLER_NAME%

set NEED_INSTALL=1
set PY_RUN=

echo [1] Detect current python version
python -V >tmp_ver.txt 2>&1
type tmp_ver.txt
findstr /C:"Python %TARGET_PY_VER%" tmp_ver.txt >nul 2>&1
if !errorlevel! equ 0 (
    echo Detected matching Python version, skip installation
    set PY_RUN=python
    set NEED_INSTALL=0
)
del tmp_ver.txt

if !NEED_INSTALL! equ 1 (
    echo Mismatched Python version detected, starting silent install for 3.14.5
    if not exist "%INSTALLER%" (
        echo [Fatal Error] Installer file %INSTALLER_NAME% missing
        echo Full lookup path: "%INSTALLER%"
        pause
        exit /b 1
    )

    md "%PY_INSTALL_PATH%" 2>nul
    echo Target directory created: %PY_INSTALL_PATH%
    echo Installing Python, please wait...

    :: Silent install parameters, single line to avoid popup
    "%INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_doc=0 Include_launcher=1 TargetDir="%PY_INSTALL_PATH%"

    echo Waiting for installation write completion, 15s delay...
    timeout /t 15 /nobreak >nul

    if not exist "%PY_FULL_EXE%" (
        echo.
        echo ##################################################
        echo Python installation failed! Target path: "%PY_FULL_EXE%"

        echo Troubleshooting steps:

        echo 1. Admin rights required for initial Python install and venv creation

        echo 2. Temporarily disable antivirus software

        echo 3. Verify write permission on target disk

        echo ##################################################
        pause
        exit /b 2
    )
    echo Python 3.14 installation completed successfully
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

echo Virtual environment not found, creating new %VENV_NAME%
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
    echo Error: mcp_client.py file missing
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