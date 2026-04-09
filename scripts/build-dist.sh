#!/bin/bash
# Script para construir distribuibles con Briefcase

set -e  # Detener en caso de error

# Cambiar al directorio raíz del proyecto
cd "$(dirname "$0")/.."

echo "======================================"
echo "  Focus Recorder - Build Distribución"
echo "======================================"
echo ""

# Verificar que pyproject.toml existe
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml no encontrado"
    exit 1
fi

echo "Instalando Briefcase..."
pip install briefcase

echo ""
echo "Creando estructura del proyecto..."
briefcase create

echo ""
echo "Compilando aplicación..."
briefcase build

echo ""
echo "Empaquetando para distribución..."
briefcase package

echo ""
echo "======================================"
echo "¡Listo!"
echo "======================================"
echo ""
echo "El instalador/paquete está en:"
echo "  Linux: dist/Focus Recorder-*.AppImage"
echo "  Windows: dist/Focus Recorder-*.msi"
echo "  macOS: dist/Focus Recorder-*.dmg"
echo ""

