import cv2
import numpy as np
import threading
from pynput import mouse
import time
import os
import subprocess
import imageio_ffmpeg
import platform
from pathlib import Path
from dataclasses import replace

from .app.config import get_default_recording_settings
from .app.factories.capture_backend_factory import create_capture_backend
from .application.errors import RecordingEnvironmentError
from .domain.ports.capture_backend import CaptureBackend
from .domain.settings import RecordingSettings

# Importación condicional según el sistema operativo
IS_WINDOWS = platform.system() == "Windows"



class FocusRecorder:
    def __init__(self, config=None):
        self.is_windows = IS_WINDOWS
        self.mouse_controller = mouse.Controller()
        self.settings = self._coerce_settings(config)
        self.capture_backend = self._build_capture_backend()
        self.is_recording = False
        self.sw, self.sh = self._get_screen_size()
        self.raw_data = []
        self.is_clicking = False

        # Determinar la carpeta de salida según el sistema operativo
        self.output_dir = self._get_video_directory()
        
        os.makedirs(self.output_dir, exist_ok=True)
        self.filename = self._get_next_filename()

    def _get_video_directory(self):
        """
        Obtiene la carpeta de videos apropiada según la plataforma.
        Guarda en una carpeta compartida del workspace para que los archivos sean
        accesibles también desde Windows cuando se trabaja sobre /d.
        """
        return str(self.settings.output_dir)

    def _coerce_settings(self, config):
        if config is None:
            return get_default_recording_settings()

        if isinstance(config, RecordingSettings):
            return config

        if isinstance(config, dict):
            settings = get_default_recording_settings()
            updates = {}
            if "zoom" in config:
                updates["zoom"] = config["zoom"]
            if "suavidad" in config:
                updates["suavidad"] = config["suavidad"]
            if "fps" in config:
                updates["fps"] = config["fps"]
            if "output_dir" in config:
                updates["output_dir"] = Path(config["output_dir"])
            return replace(settings, **updates)

        raise TypeError("config must be None, a dict, or RecordingSettings")

    def _get_next_filename(self):
        idx = 1
        while True:
            name = os.path.join(self.output_dir, f"video_{idx}.mp4")
            if not os.path.exists(name):
                return name
            idx += 1

    def _on_click(self, x, y, button, pressed):
        self.is_clicking = pressed

    def _build_capture_backend(self) -> CaptureBackend:
        return create_capture_backend(is_windows=self.is_windows)

    def _get_screen_size(self):
        return self.capture_backend.get_screen_size()

    def _get_mouse_position(self):
        x, y = self.mouse_controller.position
        return int(x), int(y)

    def _validate_capture_backend(self):
        try:
            self.capture_backend.validate()
        except Exception as exc:
            backend_name = type(self.capture_backend).__name__
            message = (
                f"No se pudo iniciar la captura de pantalla con {backend_name}. "
                "El entorno actual no parece ser compatible con el backend de captura seleccionado."
            )
            raise RecordingEnvironmentError(message) from exc

    def start(self):
        self._validate_capture_backend()
        self.is_recording = True
        self.raw_data = []
        self.start_time = time.perf_counter()
        self.listener = mouse.Listener(on_click=self._on_click)
        self.listener.start()
        self.thread = threading.Thread(target=self._record_loop)
        self.thread.start()

    def stop(self, callback_progress=None, export_mode="full"):
        self.is_recording = False
        if hasattr(self, 'listener'):
            self.listener.stop()
        self.thread.join()
        self._render_adaptive_video(callback_progress, export_mode)

    def _record_loop(self):
        self.capture_backend.start()
        try:
            while self.is_recording:
                frame = self.capture_backend.capture_frame()
                if frame is None:
                    continue

                mx, my = self._get_mouse_position()
                ts = time.perf_counter() - self.start_time
                self.raw_data.append((frame.copy(), mx, my, self.is_clicking, ts))

                if self.is_windows:
                    time.sleep(0.001)
                else:
                    time.sleep(0.01)
        finally:
            self.capture_backend.stop()

    def _reencode_h264(self, input_path):
        """
        Re-encodea el archivo a H.264 + AAC usando el FFmpeg
        embebido en imageio-ffmpeg. Compatible con WhatsApp, Instagram, etc.
        Reemplaza el archivo original al terminar.
        """
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        tmp_path = input_path.replace(".mp4", "_h264.mp4")

        cmd = [
            ffmpeg_exe,
            "-y",                      # sobreescribir sin preguntar
            "-i", input_path,          # entrada
            "-c:v", "libx264",         # codec H.264
            "-preset", "fast",         # velocidad/calidad balance
            "-crf", "18",              # calidad alta (0=lossless, 51=peor)
            "-pix_fmt", "yuv420p",     # compatible con todos los reproductores
            "-movflags", "+faststart",  # metadata al inicio (streaming/WA)
            "-an",                     # sin audio (grabación de pantalla)
            tmp_path
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Reemplazar archivo intermedio con el H.264 final
        if os.path.exists(tmp_path):  # pragma: no cover
            os.remove(input_path)
            os.rename(tmp_path, input_path)
        elif os.path.getsize(input_path) > 0:
            # Si falló el re-encode pero el original existe, lo dejamos
            pass

    def _render_adaptive_video(self, callback_progress, export_mode):
        if not self.raw_data:
            return

        total_duration = self.raw_data[-1][4]
        target_fps = int(self.settings.fps)
        total_frames = int(total_duration * target_fps)

        # Codec para Linux/Windows (mp4v es seguro para OpenCV)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        do_full   = export_mode in ("full", "both")
        do_tiktok = export_mode in ("tiktok", "both")

        out_full = None
        if do_full:
            out_full = cv2.VideoWriter(self.filename, fourcc, target_fps, (self.sw, self.sh))

        out_tiktok = None
        tiktok_w = tiktok_h = 0
        tiktok_path = ""
        if do_tiktok:
            tiktok_h = self.sh
            tiktok_w = int(self.sh * 9 / 16)
            if tiktok_w % 2 != 0:  # pragma: no cover
                tiktok_w += 1
            tiktok_path = self.filename.replace(".mp4", "_tiktok.mp4")
            out_tiktok = cv2.VideoWriter(tiktok_path, fourcc, target_fps, (tiktok_w, tiktok_h))

        cam_x = float(self.sw // 2)
        cam_y = float(self.sh // 2)
        tiktok_cam_x = float(self.sw // 2)
        tiktok_cam_y = float(self.sh // 2)
        tiktok_smooth = min(self.settings.suavidad * 1.5, 1.0)

        data_ptr = 0

        # Renderizado ocupa el 80% del progreso; el re-encode el 20% restante
        render_weight = 0.8

        for f_idx in range(total_frames):
            current_time = f_idx / target_fps

            while data_ptr < len(self.raw_data) - 1 and self.raw_data[data_ptr + 1][4] < current_time:
                data_ptr += 1

            frame, mx, my, clicking, _ = self.raw_data[data_ptr]
            color = (0, 215, 255) if clicking else (255, 255, 255)
            zn = self.settings.zoom

            # ── PANTALLA COMPLETA ────────────────────────────────────────
            if do_full:
                cam_x += (mx - cam_x) * self.settings.suavidad
                cam_y += (my - cam_y) * self.settings.suavidad

                z_w = int(self.sw / zn)
                z_h = int(self.sh / zn)
                x1 = int(np.clip(cam_x - z_w // 2, 0, self.sw - z_w))
                y1 = int(np.clip(cam_y - z_h // 2, 0, self.sh - z_h))

                cropped = frame[y1:y1 + z_h, x1:x1 + z_w]
                
                if cropped.size > 0:  # pragma: no cover
                    final = cv2.resize(cropped, (self.sw, self.sh), interpolation=cv2.INTER_LANCZOS4)

                    vx = int(np.clip((mx - x1) * (self.sw / z_w), 0, self.sw - 1))
                    vy = int(np.clip((my - y1) * (self.sh / z_h), 0, self.sh - 1))
                    cv2.circle(final, (vx, vy), 8, color, -1 if clicking else 2, lineType=cv2.LINE_AA)
                    out_full.write(final)

            # ── TIKTOK 9:16 ──────────────────────────────────────────────
            if do_tiktok:
                tiktok_cam_x += (mx - tiktok_cam_x) * tiktok_smooth
                tiktok_cam_y += (my - tiktok_cam_y) * tiktok_smooth

                z_h_tt = int(self.sh / zn)
                z_w_tt = min(int(z_h_tt * 9 / 16), self.sw)
                z_h_tt = min(z_h_tt, self.sh)

                x1_tt = int(np.clip(tiktok_cam_x - z_w_tt // 2, 0, self.sw - z_w_tt))
                y1_tt = int(np.clip(tiktok_cam_y - z_h_tt // 2, 0, self.sh - z_h_tt))

                cropped_tt = frame[y1_tt:y1_tt + z_h_tt, x1_tt:x1_tt + z_w_tt]
                
                if cropped_tt.size > 0 and tiktok_w > 0 and tiktok_h > 0:  # pragma: no cover
                    final_tt = cv2.resize(cropped_tt, (tiktok_w, tiktok_h), interpolation=cv2.INTER_LANCZOS4)
                    tx = int(np.clip((mx - x1_tt) * (tiktok_w / z_w_tt), 0, tiktok_w - 1))
                    ty = int(np.clip((my - y1_tt) * (tiktok_h / z_h_tt), 0, tiktok_h - 1))
                    cv2.circle(final_tt, (tx, ty), 8, color, -1 if clicking else 2, lineType=cv2.LINE_AA)
                    out_tiktok.write(final_tt)

            if callback_progress and f_idx % 10 == 0:
                pct = int((f_idx / total_frames) * 100 * render_weight)
                callback_progress(pct)

        if out_full:
            out_full.release()
        if out_tiktok:
            out_tiktok.release()

        # ── RE-ENCODE A H.264 (compatible WhatsApp / Instagram) ──────────
        files_to_encode = []
        if do_full:
            files_to_encode.append(self.filename)
        if do_tiktok:
            files_to_encode.append(tiktok_path)

        for i, path in enumerate(files_to_encode):
            self._reencode_h264(path)
            if callback_progress:
                base = int(100 * render_weight)
                pct = base + int((i + 1) / len(files_to_encode) * (100 - base))
                callback_progress(pct)

        if callback_progress:
            callback_progress(100)
