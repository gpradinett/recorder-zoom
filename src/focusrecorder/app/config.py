from dataclasses import dataclass, replace
from pathlib import Path

from ..domain.settings import RecordingSettings


@dataclass(frozen=True)
class AppConfig:
    default_recording_settings: RecordingSettings


def get_default_output_dir() -> Path:
    return Path.home() / "Desktop" / "videos"


def get_default_recording_settings() -> RecordingSettings:
    return RecordingSettings(
        zoom=1.8,
        suavidad=0.05,
        fps=60,
        output_dir=get_default_output_dir(),
    )


def get_app_config() -> AppConfig:
    return AppConfig(default_recording_settings=get_default_recording_settings())


def with_recording_overrides(
    settings: RecordingSettings,
    *,
    zoom: float | None = None,
    suavidad: float | None = None,
    fps: int | None = None,
) -> RecordingSettings:
    updates = {}
    if zoom is not None:
        updates["zoom"] = zoom
    if suavidad is not None:
        updates["suavidad"] = suavidad
    if fps is not None:
        updates["fps"] = fps
    return replace(settings, **updates)
