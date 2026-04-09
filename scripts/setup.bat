@echo off
setlocal enabledelayedexpansion

REM Cambiar al directorio raíz del proyecto
cd /d "%~dp0.."

echo ======================================
echo   Focus Recorder - Instalacion
echo ======================================
echo.

REM Verificar Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [X] Error: Python no esta instalado
    echo    Descargalo desde: https://www.python.org/downloads/
    echo    IMPORTANTE: Marca "Add Python to PATH" durante instalacion
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] !PYTHON_VERSION! detectado
echo.

REM Crear entorno virtual
echo [*] Creando entorno virtual...
if exist "venv" (
    echo    ^(^!^) El entorno virtual ya existe. Deseas recrearlo? ^(S/N^)
    set /p response=
    if /i "!response!"=="S" (
        rmdir /s /q venv
        python -m venv venv
        echo    [OK] Entorno virtual recreado
    ) else (
        echo    [i] Usando entorno virtual existente
    )
) else (
    python -m venv venv
    echo    [OK] Entorno virtual creado
)
echo.

REM Activar entorno virtual
echo [*] Activando entorno virtual...
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo    [X] Error al activar entorno virtual
    pause
    exit /b 1
)
echo    [OK] Entorno activado
echo.

REM Actualizar pip
echo [*] Actualizando pip...
python -m pip install --upgrade pip --quiet
echo    [OK] pip actualizado
echo.

REM Instalar dependencias
echo [*] Instalando dependencias...
echo    (Esto puede tardar varios minutos...)
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo    [X] Error al instalar dependencias
    pause
    exit /b 1
)
echo    [OK] Dependencias instaladas correctamente
echo.

REM Instalar el paquete en modo editable
echo [*] Instalando el paquete en modo desarrollo...
pip install -e .
echo    [OK] Paquete instalado correctamente
echo.

REM Crear directorio de videos
echo [*] Creando directorio de videos...
if not exist "videos" mkdir videos
echo    [OK] Directorio creado
echo.

REM Prueba de importaciones
echo [*] Probando importaciones...
python -c "import sys; from PyQt6 import QtWidgets; print('   [OK] PyQt6'); import cv2; print('   [OK] OpenCV'); import numpy; print('   [OK] NumPy'); import pyautogui; print('   [OK] PyAutoGUI'); import pynput; print('   [OK] Pynput'); import dxcam; print('   [OK] DXCam'); import mss; print('   [OK] MSS'); print(''); print('[OK] Todas las dependencias se importaron correctamente!')"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [X] Hubo problemas con las dependencias
    pause
    exit /b 1
)
echo.

REM Crear script de ejecución
echo [*] Creando script de ejecucion...
(
echo @echo off
echo cd /d "%%~dp0.."
echo call venv\Scripts\activate.bat
echo python -m focusrecorder
echo pause
) > "scripts\run.bat"
echo    [OK] Script creado: scripts\run.bat
echo.

echo ======================================
echo   [OK] Instalacion completada!
echo ======================================
echo.
echo Para ejecutar la aplicacion:
echo   run.bat
echo.
echo O manualmente:
echo   venv\Scripts\activate.bat
echo   python -m focusrecorder
echo.
pause
