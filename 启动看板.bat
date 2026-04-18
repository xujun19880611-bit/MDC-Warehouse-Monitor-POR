@echo off
setlocal
:: 1. 自动进入当前 .bat 文件所在的目录，无论路径是否有空格或中文
cd /d "%~dp0"

echo ==========================================
echo    正在启动 MDC 全仓库智能监控系统...
echo ==========================================

:: 2. 使用引号包裹路径，并指定当前的 .py 文件名
:: 注意：如果您的文件名不是 warehouse_app.py，请修改下方最后的文件名
"C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m streamlit run "Total WH.py"

:: 3. 如果启动失败，给出提示
if %errorlevel% neq 0 (
    echo.
    echo [错误] 启动失败！请检查：
    echo 1. warehouse_app.py 是否在当前文件夹下？
    echo 2. 是否已安装 streamlit (pip install streamlit)？
    echo.
    pause
)

pause