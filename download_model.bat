@echo off
chcp 65001 >nul
echo 正在启动模型下载脚本...
echo ----------------------------------------------------

if not exist "runtime\python.exe" (
    echo [错误] 未找到运行环境！
    echo 请先运行 setup_env.bat 初始化环境。
    echo.
    pause
    exit /b 1
)

"runtime\python.exe" download_model.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 下载过程中出现问题。
) else (
    echo.
    echo [成功] 模型下载/校验完成。
)

echo.
echo 按任意键退出...
pause >nul
