from ...domain.ports.capture_backend import CaptureBackend
from ...infrastructure.capture.dxcam_backend import DxcamCaptureBackend, dxcam
from ...infrastructure.capture.mss_backend import MssCaptureBackend


def create_capture_backend(*, is_windows: bool) -> CaptureBackend:
    if is_windows and dxcam is not None:
        return DxcamCaptureBackend()
    return MssCaptureBackend()
