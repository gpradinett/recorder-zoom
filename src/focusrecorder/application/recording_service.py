from dataclasses import dataclass

from ..config.settings import RecordingSettings
from ..recorder import FocusRecorder


@dataclass(frozen=True)
class StartRecordingResult:
    recorder: FocusRecorder
    filename: str


class RecordingService:
    def start_recording(self, settings: RecordingSettings) -> StartRecordingResult:
        recorder = FocusRecorder(config=settings)
        recorder.start()
        return StartRecordingResult(recorder=recorder, filename=recorder.filename)

    def stop_recording(self, recorder: FocusRecorder, *, callback_progress=None, export_mode="full"):
        recorder.stop(callback_progress=callback_progress, export_mode=export_mode)
        return {
            "full_path": recorder.filename if export_mode in ("full", "both") else "",
            "tiktok_path": recorder.filename.replace(".mp4", "_tiktok.mp4") if export_mode in ("tiktok", "both") else "",
        }
