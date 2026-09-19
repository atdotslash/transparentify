@echo off
setlocal enabledelayedexpansion

echo =======================================================
echo   Transparentify - Compilador de ejecutable para Windows
echo =======================================================
echo.

cd /d "%~dp0\.."

echo [1/3] Verificando entorno Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta disponible en el PATH.
    pause
    exit /b 1
)

echo [2/3] Instalando dependencias necesarias...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller

echo.
echo [3/3] Generando ejecutable standalone con PyInstaller...
pyinstaller --noconfirm --windowed --onefile ^
    --name Transparentify ^
    --icon assets/icons/app.ico ^
    --add-data "assets;assets" ^
    --collect-all customtkinter ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] La compilacion ha fallado. Revisa los mensajes anteriores.
    pause
    exit /b 1
)

echo.
echo =======================================================
echo   Compilacion exitosa!
echo   Ejecutable generado en: dist\Transparentify.exe
echo =======================================================
echo.

pause
