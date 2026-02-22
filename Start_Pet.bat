@echo off
chcp 65001 >nul
echo 正在启动海小棠桌面宠物...

:: 1. 优先尝试使用项目内自带的 Embeddable Python
if exist "%~dp0runtime\pythonw.exe" (
    echo [Environment] Local runtime (runtime\pythonw.exe)
    set "PYTHON_EXE=%~dp0runtime\pythonw.exe"
    set "PYTHONPATH=%~dp0"
    goto :START
)

:: 2. 其次尝试使用开发用的虚拟环境
if exist "%~dp0.venv\Scripts\pythonw.exe" (
    echo [Environment] Dev venv (.venv\Scripts\pythonw.exe)
    set "PYTHON_EXE=%~dp0.venv\Scripts\pythonw.exe"
    set "PYTHONPATH=%~dp0"
    goto :START
)

:: 3. 最后尝试使用系统 Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [Error] Python not found!
    echo 请先安装 Python 或运行 setup_env.bat
    pause
    exit /b
)
echo [Environment] System Python (pythonw)
set "PYTHON_EXE=pythonw"
set "PYTHONPATH=%~dp0"

:START
echo ------------------------------------------
echo 正在启动主程序...
echo 请耐心等待几秒钟，不要关闭黑框。
echo 当桌宠出现后，此黑框会自动消失。
echo ------------------------------------------

:: 使用 start /wait 启动一个临时的提示框（这里简化为直接打印并等待一小会儿）
:: 然后启动 pythonw，黑框随即退出

:: 关键修改：用 start "" "%PYTHON_EXE%" 启动，不加 /wait，让脚本继续往下走并退出
start "" "%PYTHON_EXE%" "%~dp0src/main.py"

:: 等待 1 秒给用户看一眼提示，然后自动关闭黑框
timeout /t 1 >nul
exit
