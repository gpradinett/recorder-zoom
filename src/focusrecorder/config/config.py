from dataclasses import dataclass, replace
from pathlib import Path

from .settings import RecordingSettings, UISettings, UserPreferences
from .preferences import load_user_preferences, save_user_preferences
from .constants import (
    DEFAULT_ZOOM,
    DEFAULT_SUAVIDAD,
    DEFAULT_FPS,
    DEFAULT_EXPORT_MODE,
)
from ..utils.system_paths import get_default_output_dir


@dataclass(frozen=True)
class AppConfig:
    user_preferences: UserPreferences


def get_default_recording_settings() -> RecordingSettings:
    """Get default recording settings using constants."""
    return RecordingSettings(
        zoom=DEFAULT_ZOOM,
        suavidad=DEFAULT_SUAVIDAD,
        fps=DEFAULT_FPS,
        output_dir=get_default_output_dir(),
    )


def get_default_ui_settings() -> UISettings:
    """Get default UI settings using constants."""
    return UISettings(export_mode=DEFAULT_EXPORT_MODE)


def load_user_preferences_as_settings() -> UserPreferences:
    """Load user preferences from disk and convert to Settings objects."""
    prefs = load_user_preferences()
    
    recording_settings = RecordingSettings(
        zoom=prefs["zoom"],
        suavidad=prefs["suavidad"],
        fps=prefs["fps"],
        output_dir=Path(prefs["output_dir"]),
    )
    
    ui_settings = UISettings(export_mode=prefs["export_mode"])
    
    return UserPreferences(recording=recording_settings, ui=ui_settings)


def save_user_preferences_from_settings(preferences: UserPreferences) -> None:
    """Save Settings objects to disk as JSON."""
    prefs_dict = {
        "zoom": preferences.recording.zoom,
        "suavidad": preferences.recording.suavidad,
        "fps": preferences.recording.fps,
        "output_dir": str(preferences.recording.output_dir),
        "export_mode": preferences.ui.export_mode,
    }
    save_user_preferences(prefs_dict)


def get_app_config() -> AppConfig:
    """Get application configuration, loading user preferences from disk."""
    user_prefs = load_user_preferences_as_settings()
    return AppConfig(user_preferences=user_prefs)


def with_recording_overrides(
    settings: RecordingSettings,
    *,
    zoom: float | None = None,
    suavidad: float | None = None,
    fps: int | None = None,
) -> RecordingSettings:
    """Create a new RecordingSettings with overridden values."""
    updates = {}
    if zoom is not None:
        updates["zoom"] = zoom
    if suavidad is not None:
        updates["suavidad"] = suavidad
    if fps is not None:
        updates["fps"] = fps
    return replace(settings, **updates)
