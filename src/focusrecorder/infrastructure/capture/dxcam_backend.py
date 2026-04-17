import ctypes

from ...domain.ports.capture_backend import CaptureBackend

try:
    import dxcam
except ImportError:  # pragma: no cover - depends on platform/runtime
    dxcam = None


class DxcamCaptureBackend(CaptureBackend):
    _camera_instance = None

    def __init__(self):
        if dxcam is None:
            raise RuntimeError("dxcam is not available")

        if DxcamCaptureBackend._camera_instance is None:
            DxcamCaptureBackend._camera_instance = dxcam.create(output_color="BGR")
        self.camera = DxcamCaptureBackend._camera_instance

    def get_screen_size(self) -> tuple[int, int]:
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    def start(self):
        self.camera.start(target_fps=0)

    def capture_frame(self):
        return self.camera.get_latest_frame()

    def stop(self):
        self.camera.stop()
