import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QSlider, QSpinBox,
                             QProgressBar, QButtonGroup, QRadioButton, QHBoxLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from .app.config import get_app_config, with_recording_overrides
from .application.errors import RecordingEnvironmentError
from .application.recording_service import RecordingService

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"


class RenderThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str, str)

    def __init__(self, recording_service, recorder, export_mode):
        super().__init__()
        self.recording_service = recording_service
        self.recorder = recorder
        self.export_mode = export_mode  # "full", "tiktok", "both"

    def run(self):
        result = self.recording_service.stop_recording(
            self.recorder,
            callback_progress=self.progress.emit,
            export_mode=self.export_mode,
        )
        full = result["full_path"]
        tiktok = result["tiktok_path"]
        self.finished.emit(full, tiktok)


class FocusApp(QWidget):
    def __init__(self):
        super().__init__()
        self.app_config = get_app_config()
        self.recording_service = RecordingService()
        self.recorder = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Video Recorder Control Panel")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumWidth(320)
        self.setMaximumWidth(320)

        layout = QVBoxLayout()
        layout.setSpacing(6)

        # --- CARPETA DE DESTINO ---
        layout.addWidget(QLabel("📁 Carpeta de destino:"))
        video_dir = self._get_video_directory_display()
        dir_label = QLabel(video_dir)
        dir_label.setWordWrap(True)
        dir_label.setStyleSheet("color: #666; font-size: 10px; padding: 2px;")
        layout.addWidget(dir_label)

        # --- MODO DE EXPORTACIÓN ---
        layout.addWidget(QLabel("Exportar como:"))

        self.export_group = QButtonGroup(self)
        radio_layout = QHBoxLayout()

        self.radio_full   = QRadioButton("Pantalla completa")
        self.radio_tiktok = QRadioButton("TikTok 9:16")
        self.radio_both   = QRadioButton("Ambos")
        self.radio_full.setChecked(True)

        self.export_group.addButton(self.radio_full,   0)
        self.export_group.addButton(self.radio_tiktok, 1)
        self.export_group.addButton(self.radio_both,   2)

        radio_layout.addWidget(self.radio_full)
        radio_layout.addWidget(self.radio_tiktok)
        radio_layout.addWidget(self.radio_both)
        layout.addLayout(radio_layout)

        # --- AJUSTE DE ZOOM ---
        layout.addWidget(QLabel("Nivel de Zoom:"))
        self.zoom_spin = QSpinBox()
        self.zoom_spin.setRange(10, 40)
        self.zoom_spin.setValue(int(self.app_config.default_recording_settings.zoom * 10))
        self.zoom_spin.setPrefix("x ")
        self.zoom_spin.setSingleStep(2)
        layout.addWidget(self.zoom_spin)

        # --- AJUSTE DE SUAVIDAD ---
        layout.addWidget(QLabel("Suavidad de Cámara (Inercia):"))
        self.smooth_slider = QSlider(Qt.Orientation.Horizontal)
        self.smooth_slider.setRange(1, 20)
        self.smooth_slider.setValue(int(self.app_config.default_recording_settings.suavidad * 100))
        layout.addWidget(self.smooth_slider)

        # --- AJUSTE DE FPS ---
        layout.addWidget(QLabel("FPS del Video Final:"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(24, 60)
        self.fps_spin.setValue(self.app_config.default_recording_settings.fps)
        layout.addWidget(self.fps_spin)

        # --- ESTADO ---
        self.status = QLabel("Listo")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setWordWrap(True)
        self.status.setMinimumHeight(40)
        layout.addWidget(self.status)

        # --- PROGRESO ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # --- BOTÓN PRINCIPAL ---
        self.btn = QPushButton("INICIAR GRABACIÓN")
        self.btn.clicked.connect(self.toggle)
        self.btn.setFixedHeight(50)
        self.btn.setStyleSheet("background: #28a745; color: white; font-weight: bold;")
        layout.addWidget(self.btn)

        self.setLayout(layout)
        self.adjustSize()

    def _get_video_directory_display(self):
        """Obtiene la ruta de videos para mostrar en la UI"""
        return str(self.app_config.default_recording_settings.output_dir)

    def _get_export_mode(self):
        return {0: "full", 1: "tiktok", 2: "both"}[self.export_group.checkedId()]

    def _set_controls_enabled(self, enabled):
        for w in (self.zoom_spin, self.smooth_slider, self.fps_spin,
                  self.radio_full, self.radio_tiktok, self.radio_both):
            w.setEnabled(enabled)

    def toggle(self):
        if self.recorder is None or not self.recorder.is_recording:
            self._set_controls_enabled(False)

            settings = with_recording_overrides(
                self.app_config.default_recording_settings,
                zoom=self.zoom_spin.value() / 10.0,
                suavidad=self.smooth_slider.value() / 100.0,
                fps=self.fps_spin.value(),
            )
            try:
                result = self.recording_service.start_recording(settings)
                self.recorder = result.recorder
            except RecordingEnvironmentError as exc:
                self.recorder = None
                self._set_controls_enabled(True)
                self.status.setText(f"❌ {exc}")
                return
            except Exception as exc:
                self.recorder = None
                self._set_controls_enabled(True)
                self.status.setText(f"❌ Error inesperado al iniciar: {exc}")
                return

            self.btn.setText("DETENER Y PROCESAR")
            self.btn.setStyleSheet("background: #dc3545; color: white; font-weight: bold;")
            # Mostrar solo el nombre del archivo, no la ruta completa
            filename = os.path.basename(result.filename)
            self.status.setText(f"🔴 Grabando...\n{filename}")

        else:
            self.btn.setEnabled(False)
            mode = self._get_export_mode()
            label = {"full": "pantalla completa", "tiktok": "TikTok 9:16", "both": "ambos formatos"}[mode]
            self.status.setText(f"⚙️ Renderizando {label}...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            self.render_thread = RenderThread(self.recording_service, self.recorder, export_mode=mode)
            self.render_thread.progress.connect(self.progress_bar.setValue)
            self.render_thread.finished.connect(self.on_finished)
            self.render_thread.start()

    def on_finished(self, full_path, tiktok_path):
        self.btn.setEnabled(True)
        self.btn.setText("INICIAR GRABACIÓN")
        self.btn.setStyleSheet("background: #28a745; color: white; font-weight: bold;")

        lines = ["✅ Guardado:"]
        if full_path:
            # Mostrar solo el nombre del archivo
            filename = os.path.basename(full_path)
            lines.append(f"📺 {filename}")
        if tiktok_path:
            # Mostrar solo el nombre del archivo
            filename = os.path.basename(tiktok_path)
            lines.append(f"📱 {filename}")
        self.status.setText("\n".join(lines))

        self.progress_bar.setVisible(False)
        self._set_controls_enabled(True)


def run():
    """Entry point for the application"""
    app = QApplication(sys.argv)
    ex = FocusApp()
    ex.show()
    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover
    run()

