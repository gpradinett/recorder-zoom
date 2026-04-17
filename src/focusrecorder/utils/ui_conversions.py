"""Utilidades para conversiones entre valores de UI y valores de grabación."""


def recording_zoom_to_ui(zoom: float) -> int:
    """
    Convierte el nivel de zoom de grabación (1.0-4.0) a valor de UI (10-40).
    
    Args:
        zoom: Nivel de zoom en formato de grabación (1.0 = sin zoom, 4.0 = zoom máximo)
    
    Returns:
        Valor entero para spinbox de UI (10-40)
    """
    return int(zoom * 10)


def ui_zoom_to_recording(ui_value: int) -> float:
    """
    Convierte el valor de UI (10-40) a nivel de zoom de grabación (1.0-4.0).
    
    Args:
        ui_value: Valor del spinbox de UI (10-40)
    
    Returns:
        Nivel de zoom en formato de grabación (1.0-4.0)
    """
    return ui_value / 10.0


def recording_suavidad_to_ui(suavidad: float) -> int:
    """
    Convierte la suavidad de grabación (0.01-0.20) a valor de slider de UI (1-20).
    
    Args:
        suavidad: Nivel de suavidad en formato de grabación (0.01-0.20)
    
    Returns:
        Valor entero para slider de UI (1-20)
    """
    return int(suavidad * 100)


def ui_suavidad_to_recording(ui_value: int) -> float:
    """
    Convierte el valor de slider de UI (1-20) a suavidad de grabación (0.01-0.20).
    
    Args:
        ui_value: Valor del slider de UI (1-20)
    
    Returns:
        Nivel de suavidad en formato de grabación (0.01-0.20)
    """
    return ui_value / 100.0
