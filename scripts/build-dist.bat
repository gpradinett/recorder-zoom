@echo off
setlocal enabledelayedexpansion

REM Script para construir distribuibles con Briefcase

REM Cambiar al directorio raíz del proyecto
cd /d "%~dp0.."

echo ======================================
echo   Focus Recorder - Build Distribucion
echo ======================================
echo.

REM Verificar que pyproject.toml existe
if not exist "pyproject.toml" (
    echo Error: pyproject.toml no encontrado
    pause
    exit /b 1
)

REM Activar entorno virtual
echo Activando entorno virtual...
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo Error al activar entorno virtual
    pause
    exit /b 1
)
echo.

echo Instalando Briefcase...
pip install briefcase
if %ERRORLEVEL% NEQ 0 (
    echo Error al instalar Briefcase
    pause
    exit /b 1
)
echo.

echo Creando estructura del proyecto...
briefcase create
if %ERRORLEVEL% NEQ 0 (
    echo Error al crear estructura del proyecto
    pause
    exit /b 1
)
echo.

echo Compilando aplicacion...
briefcase build
if %ERRORLEVEL% NEQ 0 (
    echo Error al compilar la aplicacion
    pause
    exit /b 1
)
echo.

echo Empaquetando para distribucion...
briefcase package
if %ERRORLEVEL% NEQ 0 (
    echo Error al empaquetar
    pause
    exit /b 1
)
echo.

echo ======================================
echo ¡Listo!
echo ======================================
echo.
echo El instalador/paquete esta en:
echo   Windows: dist/Focus Recorder-*.msi
echo.

pause
