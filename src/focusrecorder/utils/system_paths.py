"""Utilidades para manejo de rutas del sistema específicas de cada plataforma."""
import platform
from pathlib import Path

from ..config.constants import DEFAULT_OUTPUT_FOLDER_NAME


def get_config_directory() -> Path:
    """
    Obtiene el directorio de configuración específico de la plataforma.
    
    Returns:
        Path al directorio de configuración:
        - Windows: %APPDATA%/Roaming/FocusRecorder
        - macOS: ~/Library/Application Support/FocusRecorder
        - Linux: ~/.config/FocusRecorder
    
    Notes:
        Crea el directorio si no existe.
    """
    system = platform.system()
    
    if system == "Windows":
        # Windows: %APPDATA%\FocusRecorder
        base = Path.home() / "AppData" / "Roaming"
    elif system == "Darwin":
        # macOS: ~/Library/Application Support/FocusRecorder
        base = Path.home() / "Library" / "Application Support"
    else:
        # Linux: ~/.config/FocusRecorder
        base = Path.home() / ".config"
    
    config_dir = base / "FocusRecorder"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_default_output_dir() -> Path:
    """
    Obtiene el directorio de salida por defecto para videos.
    
    Returns:
        Path al directorio de salida por defecto (Desktop/FocusRecorder_Videos)
    """
    return Path.home() / "Desktop" / DEFAULT_OUTPUT_FOLDER_NAME
