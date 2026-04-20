from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FrameSample:
    frame: Any
    mouse_x: int
    mouse_y: int
    is_clicking: bool
    timestamp: float

    def as_tuple(self):
        return (self.frame, self.mouse_x, self.mouse_y, self.is_clicking, self.timestamp)


@dataclass
class RecordingSessionState:
    is_recording: bool = False
    is_clicking: bool = False
    start_time: float = 0.0
    mouse_data: list = field(default_factory=list)  # (mx, my, clicking, ts) — sin frames
    latest_frame: Any = None
    latest_mx: int = 0
    latest_my: int = 0

    def reset(self, start_time: float) -> None:
        self.is_recording = True
        self.is_clicking = False
        self.start_time = start_time
        self.mouse_data = []
        self.latest_frame = None
        self.latest_mx = 0
        self.latest_my = 0

    def stop(self) -> None:
        self.is_recording = False

    def set_clicking(self, pressed: bool) -> None:
        self.is_clicking = pressed

    def append_sample(self, sample: FrameSample) -> None:
        self.mouse_data.append(
            (sample.mouse_x, sample.mouse_y, sample.is_clicking, sample.timestamp)
        )
        self.latest_frame = sample.frame
        self.latest_mx = sample.mouse_x
        self.latest_my = sample.mouse_y
