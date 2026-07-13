@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo    PDF Translator
echo    Перевод PDF с сохранением форматирования
echo ============================================
echo.

REM Проверка Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Python не найден!
    echo Установите Python 3.10+ с https://www.python.org/
    pause
    exit /b 1
)

REM Проверка и установка зависимостей
echo Запуск проверки зависимостей...
python "%~dp0setup.py" --auto
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ОШИБКА] Не удалось установить зависимости.
    pause
    exit /b 1
)

echo.
echo Запуск PDF Translator...
python "%~dp0main.py"

pause