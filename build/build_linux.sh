#!/usr/bin/env bash
set -e

echo "======================================================="
echo "  Transparentify - Script de compilación para Linux    "
echo "======================================================="
echo ""

# Navegar a la raíz del proyecto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "[1/3] Verificando entorno Python..."
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 no está instalado o no se encuentra en el PATH."
    exit 1
fi
python3 --version

echo "[2/3] Instalando dependencias necesarias..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt pyinstaller

echo ""
echo "[3/3] Generando binario standalone con PyInstaller..."
pyinstaller --noconfirm --windowed --onefile \
    --name Transparentify \
    --add-data "assets:assets" \
    --collect-all customtkinter \
    main.py

echo ""
echo "======================================================="
echo "  Compilación exitosa!"
echo "  Binario generado en: dist/Transparentify"
echo "======================================================="
echo ""
echo "Para ejecutar:"
echo "  chmod +x dist/Transparentify"
echo "  ./dist/Transparentify"
echo ""
echo "Nota para AppImage (opcional):"
echo "  Puedes empaquetar la carpeta dist con appimagetool si deseas un .AppImage portable."
