import os
import numpy as np
import cv2
from unittest.mock import MagicMock

from focusrecorder.recorder import FocusRecorder
import focusrecorder.recorder as recorder_module
from focusrecorder.config.settings import RecordingSettings

def test_recorder_full_rendering_workflow(monkeypatch, tmp_path):
    monkeypatch.setattr(recorder_module.Path, "home", lambda: tmp_path)
    
    settings = RecordingSettings(
        zoom=2.0, suavidad=0.5, fps=10, 
        output_dir=tmp_path / "Desktop" / "videos"
    )
    rec = FocusRecorder(config=settings)
    rec.capture_backend = MagicMock()
    
    def fake_reencode(path):
        pass

    monkeypatch.setattr(rec, "_reencode_h264", fake_reencode)

    blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    rec.raw_data = [
        (blank_frame.copy(), 320, 240, False, 0.0),
        (blank_frame.copy(), 320, 240, True, 1.0),
        (blank_frame.copy(), 100, 100, False, 2.0),
    ]
    
    writer_calls = []
    class FakeVideoWriter:
        def __init__(self, filename, fourcc, fps, frameSize):
            self.filename = filename
            writer_calls.append(("init", filename, fps, frameSize))
        def write(self, frame):
            writer_calls.append(("write", id(self)))
        def release(self):
            writer_calls.append(("release", id(self)))
            with open(self.filename, 'w') as f:
                f.write("mockvideo")

    monkeypatch.setattr(cv2, "VideoWriter", FakeVideoWriter)
    monkeypatch.setattr(cv2, "VideoWriter_fourcc", lambda *args: "mp4v")

    emitted_progress = []
    
    rec._render_adaptive_video(callback_progress=emitted_progress.append, export_mode="both")
    
    assert len(writer_calls) > 0
    assert len(emitted_progress) > 0
    assert emitted_progress[-1] == 100


def test_recorder_full_various_modes(monkeypatch, tmp_path):
    monkeypatch.setattr(recorder_module.Path, "home", lambda: tmp_path)
    
    rec = FocusRecorder(config={"zoom": 2.0, "suavidad": 0.5, "fps": 10})
    rec.capture_backend = MagicMock()
    
    monkeypatch.setattr(rec, "_reencode_h264", lambda x: None)
    monkeypatch.setattr(cv2, "VideoWriter", MagicMock())
    monkeypatch.setattr(cv2, "VideoWriter_fourcc", lambda *args: "mp4v")    
    
    rec.raw_data = []
    rec._render_adaptive_video(None, "both")
    
    blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    rec.raw_data = [
        (blank_frame.copy(), 320, 240, False, 0.0),
        (blank_frame.copy(), 320, 240, True, 1.0)
    ]

    rec._render_adaptive_video(None, "full")
    rec._render_adaptive_video(None, "tiktok")


def test_recorder_reencode_fails_gracefully(monkeypatch, tmp_path):
    monkeypatch.setattr(recorder_module.Path, "home", lambda: tmp_path)
    rec = FocusRecorder(config={"zoom": 2.0, "suavidad": 0.5, "fps": 10})
    rec.capture_backend = MagicMock()

    monkeypatch.setattr(recorder_module, "subprocess", MagicMock())
    mock_os = MagicMock()
    monkeypatch.setattr(recorder_module, "os", mock_os)
    
    mock_os.path.exists.return_value = False
    mock_os.path.getsize.return_value = 100
    
    rec._reencode_h264("fake_path.mp4")
    
    mock_os.path.getsize.return_value = 0
    rec._reencode_h264("fake_path2.mp4")
    
    assert recorder_module.subprocess.run.called


def test_recorder_os_logic(monkeypatch, tmp_path):
    monkeypatch.setattr(recorder_module.Path, "home", lambda: tmp_path)
    rec = FocusRecorder(config={"zoom": 2.0, "suavidad": 0.5, "fps": 10})
    assert rec.settings.zoom == 2.0


def test_recorder_stop_no_listener(monkeypatch, tmp_path):
    monkeypatch.setattr(recorder_module.Path, "home", lambda: tmp_path)
    rec = FocusRecorder(config={"zoom": 2.0, "suavidad": 0.5, "fps": 10})
    rec.is_recording = True
    rec.thread = MagicMock()
    rec._render_adaptive_video = MagicMock()
    rec.capture_backend = MagicMock()
    
    rec.stop(None, "full")
    rec._render_adaptive_video.assert_called_once()
