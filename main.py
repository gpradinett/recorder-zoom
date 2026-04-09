#!/usr/bin/env python3
"""
Wrapper para ejecutar Focus Recorder desde la raíz del proyecto
"""
import sys
from pathlib import Path

# Agregar src/ al path para permitir imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    from focusrecorder import main
    main.run()
