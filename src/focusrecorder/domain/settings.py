from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RecordingSettings:
    zoom: float
    suavidad: float
    fps: int
    output_dir: Path
