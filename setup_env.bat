@echo off
chcp 65001 >nul
echo 正在准备环境构建脚本...
echo ----------------------------------------------------
echo 注意：
echo 1. 此过程需要连接互联网下载 Python (约10MB) 和依赖项。
echo 2. 如果下载速度过慢，请检查网络。
echo 3. 安装完成后会自动创建 runtime 文件夹。
echo ----------------------------------------------------
echo.

:: 使用 Bypass 策略强制运行 PowerShell 脚本，防止权限报错
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_env.ps1"

if %errorlevel% neq 0 (
    echo.
    echo [错误] 脚本执行失败！请检查上方红色报错信息。
    echo 常见原因：
    echo - 网络连接失败 (无法下载 Python)
    echo - 磁盘空间不足
    echo - 目录权限不足
) else (
    echo.
    echo [成功] 环境已就绪。
    echo.
    echo 接下来，你可以运行 download_model.bat 来下载大模型。
    echo 或者直接将模型文件放入 modle/ 文件夹中。
    echo.
    echo 之后即可运行 Start_Pet.bat 来启动程序。
)

echo.
echo 按任意键退出...
pause >nul
