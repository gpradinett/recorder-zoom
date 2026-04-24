from __future__ import annotations

from typing import TYPE_CHECKING

from ..config.settings import RecordingSettings
from .dto import StartRecordingResult, StopRecordingResult

if TYPE_CHECKING:
    from ..recorder import FocusRecorder


class RecordingService:
    def start_recording(self, settings: RecordingSettings) -> StartRecordingResult:
        from ..recorder import FocusRecorder

        recorder = FocusRecorder(config=settings)
        recorder.start()
        return StartRecordingResult(recorder=recorder, filename=recorder.filename)

    def stop_recording(self, recorder: FocusRecorder, *, callback_progress=None, export_mode="full"):
        recorder.stop(callback_progress=callback_progress, export_mode=export_mode)
        return StopRecordingResult(
            full_path=recorder.filename if export_mode in ("full", "both") else "",
            tiktok_path=recorder.filename.replace(".mp4", "_tiktok.mp4") if export_mode in ("tiktok", "both") else "",
        )
