from abc import ABC, abstractmethod


class CaptureBackend(ABC):
    @abstractmethod
    def get_screen_size(self) -> tuple[int, int]:
        raise NotImplementedError

    @abstractmethod
    def capture_frame(self):
        raise NotImplementedError

    def start(self):
        """Optional hook for stateful backends."""

    def validate(self):
        """Optional preflight validation hook."""

    def stop(self):
        """Optional hook for stateful backends."""
