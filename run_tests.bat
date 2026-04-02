@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   岁月笺影 - 自动化测试套件启动器
echo ========================================
echo.

REM 检查是否在虚拟环境中
python -c "import sys; print('Python路径:', sys.executable)" 2>nul
if errorlevel 1 (
    echo ❌ Python环境检查失败
    echo 请确保已激活测试虚拟环境
    pause
    exit /b 1
)

REM 运行完整测试套件
echo 🚀 启动完整自动化测试套件...
echo.
python tests/run_complete_test_suite.py

REM 检查执行结果
if errorlevel 1 (
    echo.
    echo ❌ 测试执行失败，请检查错误信息
) else (
    echo.
    echo ✅ 测试执行完成
)

echo.
echo 📄 测试报告位置:
echo   综合报告: tests\test-results\comprehensive_test_report.json
echo.
pause