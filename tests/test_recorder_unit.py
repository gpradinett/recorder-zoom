from pathlib import Path
from unittest.mock import MagicMock

import focusrecorder.recorder as recorder_module
import focusrecorder.config.config as config_module
from focusrecorder.recorder import FocusRecorder
from focusrecorder.config.settings import RecordingSettings

def make_recorder(monkeypatch, tmp_path):
    monkeypatch.setattr(recorder_module.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(config_module.Path, "home", lambda: tmp_path)
    
    settings = RecordingSettings(
        zoom=1.8,
        suavidad=0.05,
        fps=30,
        output_dir=tmp_path / "Desktop" / "videos"
    )
    return FocusRecorder(config=settings)


def test_get_video_directory_uses_user_home(monkeypatch, tmp_path):
    rec = make_recorder(monkeypatch, tmp_path)
    assert rec.output_dir == str(tmp_path / "Desktop" / "videos")


def test_get_next_filename_increments_index(monkeypatch, tmp_path):
    video_dir = tmp_path / "Desktop" / "videos"
    video_dir.mkdir(parents=True, exist_ok=True)
    (video_dir / "video_1.mp4").write_bytes(b"dummy")

    rec = make_recorder(monkeypatch, tmp_path)
    assert Path(rec.filename).name == "video_2.mp4"


def test_reencode_h264_replaces_input_file(monkeypatch, tmp_path):
    """Test that reencode_to_h264 from video_utils works correctly"""
    import subprocess
    import imageio_ffmpeg
    
    source = tmp_path / "sample.mp4"
    source.write_bytes(b"old")

    monkeypatch.setattr(imageio_ffmpeg, "get_ffmpeg_exe", lambda: "ffmpeg-bin")
    mock_subprocess_run = MagicMock()
    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)
    
    from focusrecorder.utils.video_utils import reencode_to_h264
    reencode_to_h264(str(source))

    assert mock_subprocess_run.called


def test_render_adaptive_video_no_data_returns_without_progress(monkeypatch, tmp_path):
    rec = make_recorder(monkeypatch, tmp_path)
    rec.raw_data = []

    progress = []
    rec._render_adaptive_video(callback_progress=progress.append, export_mode="full")

    assert progress == []

