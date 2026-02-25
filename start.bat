@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo GPS Photo Overlay v3.0
echo ========================

python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден. Установите Python 3.10+
    pause
    exit /b 1
)

python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo Устанавливаю зависимости...
    pip install -r requirements.txt
    echo.
)

python main.py
if errorlevel 1 (
    echo.
    echo [ОШИБКА] Программа завершилась с ошибкой.
    pause
)
