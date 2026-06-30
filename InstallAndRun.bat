@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ====================== 配置区 ======================
set TARGET_PY_VER=3.14
set PY_INSTALL_PATH=D:\Program Files\Python\Python314
set VENV_NAME=mcp_mini_venv
set ALIYUN_PIP=https://mirrors.aliyun.com/pypi/simple/
set PY_FULL_EXE=%PY_INSTALL_PATH%\python.exe
set INSTALLER_NAME=python-3.14.5-amd64.exe
set PKG_DIR=pkg
:: ===================================================

echo ==============================================
echo MCP 自动部署脚本
echo 需要 Python %TARGET_PY_VER%，其它版本自动重装
echo Python安装路径：%PY_INSTALL_PATH%
echo 安装包文件名：%INSTALLER_NAME%
echo 虚拟环境目录：%~dp0%VENV_NAME%
echo ==============================================
echo.
cd /d "%~dp0"

:: 自动创建pkg文件夹（不存在就新建，方便你放安装包）
md "%PKG_DIR%" 2>nul
:: 拼接完整包路径：脚本目录/pkg/安装包.exe
set INSTALLER=%~dp0%PKG_DIR%\%INSTALLER_NAME%

set NEED_INSTALL=1
set PY_RUN=

echo [1] 检测当前 python -V 版本
python -V >tmp_ver.txt 2>&1
type tmp_ver.txt
findstr /C:"Python %TARGET_PY_VER%" tmp_ver.txt >nul 2>&1
if !errorlevel! equ 0 (
    echo ✅ 当前已是 Python%TARGET_PY_VER%，无需安装
    set PY_RUN=python
    set NEED_INSTALL=0
)
del tmp_ver.txt

if !NEED_INSTALL! equ 1 (
    echo ⚠️ 当前Python版本非 %TARGET_PY_VER%，开始静默安装3.14.5
    if not exist "%INSTALLER%" (
        echo 【致命错误】当前目录缺少 %INSTALLER_NAME%
        echo 完整查找路径："%INSTALLER%"
        pause
        exit /b 1
    )

    md "%PY_INSTALL_PATH%" 2>nul
    echo 已创建目录 %PY_INSTALL_PATH%
    echo 正在安装Python，请稍后...

    :: 所有参数写同一行，彻底解决换行^失效弹出界面问题
    "%INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_doc=0 Include_launcher=1 TargetDir="%PY_INSTALL_PATH%"

    echo 等待安装写入完成，延时15秒...
    timeout /t 15 /nobreak >nul

    if not exist "%PY_FULL_EXE%" (
        echo.
        echo ##################################################
        echo Python安装失败！路径："%PY_FULL_EXE%"

        echo 请依次排查下面几种情况

        echo 1.首次打开涉及到python安装和虚拟环境创建，需要右键管理员运行，后续启动直接双击即可

        echo 2.关闭抽象的杀毒软件

        echo 3.对应盘符是否可写入

        echo ##################################################
        pause
        exit /b 2
    )
    echo ✅ Python3.14 安装完成
    set PY_RUN="%PY_FULL_EXE%"
)

:PY_OK
echo.
echo [2] 检查虚拟环境 %VENV_NAME%
set VENV_DIR=%~dp0%VENV_NAME%
set VENV_ACT=%VENV_DIR%\Scripts\activate.bat


if exist "%VENV_ACT%" (
    echo ✅ 虚拟环境已存在，跳过安装，直接启动程序
    goto RUN_PROG
)

echo ⚠️ 无虚拟环境，新建 %VENV_NAME%
%PY_RUN% -m venv %VENV_NAME%

call "%VENV_ACT%"
echo.
echo [3] 升级pip并安装依赖（阿里源）
if exist "requirements.txt" (
    python -m pip install --upgrade pip -i %ALIYUN_PIP% --trusted-host mirrors.aliyun.com
    python -m pip install -r requirements.txt -i %ALIYUN_PIP% --trusted-host mirrors.aliyun.com
) else (
    echo 未找到 requirements.txt，跳过依赖
)

:RUN_PROG
echo 启动虚拟环境
call "%VENV_ACT%"
echo.
echo [4] 启动 mcp_client.py
if not exist "mcp_client.py" (
    echo 错误：找不到 mcp_client.py
    pause
    exit /b 3
)
echo ==============================================
python mcp_client.py
echo ==============================================
echo 程序结束，按任意键关闭窗口
pause >nul
deactivate
endlocal