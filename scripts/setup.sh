#!/bin/bash

set -e  # Detener si hay errores

# Cambiar al directorio raíz del proyecto
cd "$(dirname "$0")/.."

echo "======================================"
echo "  Focus Recorder - Instalación"
echo "======================================"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 no está instalado"
    echo "   Instálalo primero: sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python $PYTHON_VERSION detectado"
echo ""

# Crear entorno virtual
echo "Creando entorno virtual..."
if [ -d "venv" ]; then
    echo "    El entorno virtual ya existe. ¿Deseas recrearlo? (s/N)"
    read -r response
    if [[ "$response" =~ ^[Ss]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        echo "   ✓ Entorno virtual recreado"
    else
        echo "    Usando entorno virtual existente"
    fi
else
    python3 -m venv venv
    echo "   ✓ Entorno virtual creado"
fi
echo ""

# Activar entorno virtual
echo "Activando entorno virtual..."
source venv/bin/activate
echo "   ✓ Entorno activado"
echo ""

# Actualizar pip
echo "Actualizando pip..."
pip install --upgrade pip --quiet
echo "   ✓ pip actualizado"
echo ""

# Instalar dependencias
echo "Instalando dependencias..."
echo "   (Esto puede tardar varios minutos...)"
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "   ✓ Dependencias instaladas correctamente"
else
    echo "    Error al instalar dependencias"
    exit 1
fi
echo ""

# Instalar el paquete en modo editable
echo "Instalando el paquete en modo desarrollo..."
pip install -e .
if [ $? -eq 0 ]; then
    echo "   ✓ Paquete instalado correctamente"
else
    echo "     El paquete no se pudo instalar (se usará PYTHONPATH)"
fi
echo ""

# Crear directorio de videos
echo "Creando directorio de videos..."
mkdir -p videos
echo "   ✓ Directorio creado"
echo ""

# Prueba de importaciones
echo "Probando importaciones..."
python3 -c "
import sys
try:
    from PyQt6 import QtWidgets
    print('   ✓ PyQt6')
    import cv2
    print('   ✓ OpenCV')
    import numpy
    print('   ✓ NumPy')
    import pyautogui
    print('   ✓ PyAutoGUI')
    import pynput
    print('   ✓ Pynput')
    import mss
    print('   ✓ MSS')
    print('')
    print('¡Todas las dependencias se importaron correctamente!')
except ImportError as e:
    print(f'   Error: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "Hubo problemas con las dependencias"
    exit 1
fi
echo ""

# Crear script de ejecución
echo "Creando script de ejecución..."
cat > run.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python -m focusrecorder
EOF
chmod +x run.sh
echo "   ✓ Script creado: run.sh"
echo ""

echo "======================================"
echo "  ¡Instalación completada!"
echo "======================================"
echo ""
echo "Para ejecutar la aplicación:"
echo "  ./run.sh"
echo ""
echo "O manualmente:"
echo "  source venv/bin/activate"
echo "  python -m focusrecorder"
echo ""
