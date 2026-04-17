import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QSlider, QSpinBox,
                             QProgressBar, QButtonGroup, QRadioButton, QHBoxLayout, QFileDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from dataclasses import replace
from pathlib import Path
from .config.config import (
    get_app_config,
    with_recording_overrides,
    save_user_preferences_from_settings,
)
from .application.errors import RecordingEnvironmentError
from .application.recording_service import RecordingService
from .config.constants import (
    UI_MIN_ZOOM,
    UI_MAX_ZOOM,
    UI_MIN_SUAVIDAD,
    UI_MAX_SUAVIDAD,
    UI_MIN_FPS,
    UI_MAX_FPS,
)
from .utils.file_utils import open_folder_in_explorer
from .utils.ui_conversions import (
    recording_zoom_to_ui,
    ui_zoom_to_recording,
    recording_suavidad_to_ui,
    ui_suavidad_to_recording,
)

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
        
        # Contenedor horizontal para label y botón
        dir_container = QHBoxLayout()
        
        video_dir = self._get_video_directory_display()
        self.dir_label = QLabel(video_dir)
        self.dir_label.setWordWrap(True)
        self.dir_label.setStyleSheet("color: #666; font-size: 10px; padding: 2px;")
        dir_container.addWidget(self.dir_label, 1)  # stretch=1 para que tome más espacio
        
        # Botón para cambiar carpeta
        self.change_dir_btn = QPushButton("📂")
        self.change_dir_btn.setFixedWidth(80)
        self.change_dir_btn.clicked.connect(self._change_output_directory)
        dir_container.addWidget(self.change_dir_btn)
        
        layout.addLayout(dir_container)

        # --- MODO DE EXPORTACIÓN ---
        layout.addWidget(QLabel("Exportar como:"))

        self.export_group = QButtonGroup(self)
        radio_layout = QHBoxLayout()

        self.radio_full   = QRadioButton("Pantalla completa")
        self.radio_tiktok = QRadioButton("TikTok 9:16")
        self.radio_both   = QRadioButton("Ambos")
        
        # Set initial export mode from user preferences
        mode_map = {"full": 0, "tiktok": 1, "both": 2}
        initial_mode = self.app_config.user_preferences.ui.export_mode
        if initial_mode == "full":
            self.radio_full.setChecked(True)
        elif initial_mode == "tiktok":
            self.radio_tiktok.setChecked(True)
        else:
            self.radio_both.setChecked(True)

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
        self.zoom_spin.setRange(UI_MIN_ZOOM, UI_MAX_ZOOM)
        self.zoom_spin.setValue(
            recording_zoom_to_ui(self.app_config.user_preferences.recording.zoom)
        )
        self.zoom_spin.setPrefix("x ")
        self.zoom_spin.setSingleStep(2)
        layout.addWidget(self.zoom_spin)

        # --- AJUSTE DE SUAVIDAD ---
        layout.addWidget(QLabel("Suavidad de Cámara (Inercia):"))
        self.smooth_slider = QSlider(Qt.Orientation.Horizontal)
        self.smooth_slider.setRange(UI_MIN_SUAVIDAD, UI_MAX_SUAVIDAD)
        self.smooth_slider.setValue(
            recording_suavidad_to_ui(self.app_config.user_preferences.recording.suavidad)
        )
        layout.addWidget(self.smooth_slider)

        # --- AJUSTE DE FPS ---
        layout.addWidget(QLabel("FPS del Video Final:"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(UI_MIN_FPS, UI_MAX_FPS)
        self.fps_spin.setValue(self.app_config.user_preferences.recording.fps)
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
        self._center_on_screen()

    def _center_on_screen(self):
        """Centra la ventana en la pantalla."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())

    def _get_video_directory_display(self):
        """Obtiene la ruta de videos para mostrar en la UI"""
        return str(self.app_config.user_preferences.recording.output_dir)

    def _get_export_mode(self):
        return {0: "full", 1: "tiktok", 2: "both"}[self.export_group.checkedId()]

    def _set_controls_enabled(self, enabled):
        for w in (self.zoom_spin, self.smooth_slider, self.fps_spin,
                  self.radio_full, self.radio_tiktok, self.radio_both, self.change_dir_btn):
            w.setEnabled(enabled)
    
    def _change_output_directory(self):
        """Abre un diálogo para seleccionar la carpeta de destino."""
        current_dir = str(self.app_config.user_preferences.recording.output_dir)
        
        new_dir = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de destino para videos",
            current_dir,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        
        if new_dir:  # Si el usuario seleccionó una carpeta (no canceló)
            new_path = Path(new_dir)
            
            # Actualizar la configuración
            from .config.settings import UserPreferences
            updated_recording = replace(
                self.app_config.user_preferences.recording,
                output_dir=new_path
            )
            updated_prefs = UserPreferences(
                recording=updated_recording,
                ui=self.app_config.user_preferences.ui
            )
            
            # Guardar preferencias
            save_user_preferences_from_settings(updated_prefs)
            
            # Actualizar config en memoria
            self.app_config = replace(self.app_config, user_preferences=updated_prefs)
            
            # Actualizar el label en la UI
            self.dir_label.setText(str(new_path))
            
            self.status.setText(f"✅ Carpeta actualizada:\n{new_path.name}")

    def toggle(self):
        if self.recorder is None or not self.recorder.is_recording:
            self._set_controls_enabled(False)
            
            # Save current settings to preferences
            self._save_current_preferences()

            settings = with_recording_overrides(
                self.app_config.user_preferences.recording,
                zoom=ui_zoom_to_recording(self.zoom_spin.value()),
                suavidad=ui_suavidad_to_recording(self.smooth_slider.value()),
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
        
        # Abrir la carpeta que contiene los videos
        output_dir = self.app_config.user_preferences.recording.output_dir
        open_folder_in_explorer(output_dir)

    def _save_current_preferences(self):
        """Save current UI settings to user preferences."""
        from .config.settings import UISettings, UserPreferences
        
        updated_recording = with_recording_overrides(
            self.app_config.user_preferences.recording,
            zoom=ui_zoom_to_recording(self.zoom_spin.value()),
            suavidad=ui_suavidad_to_recording(self.smooth_slider.value()),
            fps=self.fps_spin.value(),
        )
        
        updated_ui = UISettings(export_mode=self._get_export_mode())
        
        updated_prefs = UserPreferences(
            recording=updated_recording,
            ui=updated_ui,
        )
        
        save_user_preferences_from_settings(updated_prefs)
        
        # Update app config in memory
        self.app_config = replace(self.app_config, user_preferences=updated_prefs)


def run():
    """Entry point for the application"""
    app = QApplication(sys.argv)
    ex = FocusApp()
    ex.show()
    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover
    run()

