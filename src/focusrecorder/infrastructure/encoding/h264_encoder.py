import os
import subprocess

import imageio_ffmpeg


def reencode_to_h264(input_path: str) -> None:
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    tmp_path = input_path.replace(".mp4", "_h264.mp4")

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i",
        input_path,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-an",
        tmp_path,
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if os.path.exists(tmp_path):  # pragma: no cover
        os.remove(input_path)
        os.rename(tmp_path, input_path)
    elif os.path.getsize(input_path) > 0:
        pass


def add_audio_to_video(video_path: str, audio_path: str) -> None:
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    tmp_path = video_path.replace(".mp4", "_mixed.mp4")

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        tmp_path,
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if os.path.exists(tmp_path):  # pragma: no cover
        os.remove(video_path)
        os.rename(tmp_path, video_path)
