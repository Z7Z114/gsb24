@echo off
echo ========================================
echo  科幻小说创作头脑风暴系统
echo ========================================
echo.

echo [1/3] 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo.
echo [2/3] 安装依赖...
pip install -r requirements.txt

echo.
echo [3/3] 启动服务...
echo 服务将在 http://localhost:8000 启动
echo 按 Ctrl+C 停止服务
echo.

python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

pause
