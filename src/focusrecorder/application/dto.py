from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..recorder import FocusRecorder


@dataclass(frozen=True)
class StartRecordingResult:
    recorder: FocusRecorder
    filename: str


@dataclass(frozen=True)
class StopRecordingResult:
    full_path: str
    tiktok_path: str
