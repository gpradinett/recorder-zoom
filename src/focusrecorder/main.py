import sys
import os
import time
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QSlider, QSpinBox,
                             QProgressBar, QButtonGroup, QRadioButton, QHBoxLayout, QFileDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
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
        self.recording_start_time = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_recording_time)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("FocusSee Control Panel")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumWidth(340)
        self.setMaximumWidth(340)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # --- CARPETA DE DESTINO ---
        dest_label = QLabel("📁 Carpeta de destino")
        dest_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        layout.addWidget(dest_label)
        
        # Contenedor horizontal para label y botón
        dir_container = QHBoxLayout()
        
        video_dir = self._get_video_directory_display()
        self.dir_label = QLabel(video_dir)
        self.dir_label.setWordWrap(True)
        self.dir_label.setStyleSheet("""
            color: #555; 
            font-size: 11px; 
            padding: 8px; 
            background: white; 
            border: 1px solid #ddd;
            border-radius: 4px;
        """)
        dir_container.addWidget(self.dir_label, 1)
        
        # Botón para cambiar carpeta
        self.change_dir_btn = QPushButton("📂")
        self.change_dir_btn.setFixedWidth(40)
        self.change_dir_btn.setFixedHeight(34)
        self.change_dir_btn.setStyleSheet("""
            QPushButton {
                background: #ffc107;
                border: none;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #ffca28;
            }
            QPushButton:disabled {
                background: #e0e0e0;
            }
        """)
        self.change_dir_btn.clicked.connect(self._change_output_directory)
        dir_container.addWidget(self.change_dir_btn)
        
        layout.addLayout(dir_container)

        # --- MODO DE EXPORTACIÓN ---
        export_label = QLabel("🎬 Exportar como")
        export_label.setStyleSheet("font-weight: bold; font-size: 11px; margin-top: 5px;")
        layout.addWidget(export_label)

        self.export_group = QButtonGroup(self)
        radio_layout = QHBoxLayout()
        radio_layout.setSpacing(8)

        self.radio_full   = QRadioButton("🖥️ Pantalla\ncompleta")
        self.radio_tiktok = QRadioButton("📱 TikTok\n9:16")
        self.radio_both   = QRadioButton("📦 Ambos")
        
        # Estilos para los radio buttons
        radio_style = """
            QRadioButton {
                font-size: 10px;
                background: white;
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 10px 8px;
                text-align: center;
            }
            QRadioButton:checked {
                background: #e3f2fd;
                border: 2px solid #2196F3;
                font-weight: bold;
            }
            QRadioButton:hover {
                border-color: #90caf9;
            }
            QRadioButton:disabled {
                background: #f5f5f5;
                color: #999;
            }
            QRadioButton::indicator {
                width: 0px;
                height: 0px;
            }
        """
        
        self.radio_full.setStyleSheet(radio_style)
        self.radio_tiktok.setStyleSheet(radio_style)
        self.radio_both.setStyleSheet(radio_style)
        
        # Set initial export mode from user preferences
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
        zoom_label = QLabel("🔍 Nivel de Zoom")
        zoom_label.setStyleSheet("font-weight: bold; font-size: 11px; margin-top: 5px;")
        layout.addWidget(zoom_label)
        
        self.zoom_spin = QSpinBox()
        self.zoom_spin.setRange(UI_MIN_ZOOM, UI_MAX_ZOOM)
        self.zoom_spin.setValue(
            recording_zoom_to_ui(self.app_config.user_preferences.recording.zoom)
        )
        self.zoom_spin.setPrefix("x ")
        self.zoom_spin.setSingleStep(2)
        self.zoom_spin.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                font-size: 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QSpinBox:disabled {
                background: #f5f5f5;
                color: #999;
            }
        """)
        layout.addWidget(self.zoom_spin)

        # --- AJUSTE DE SUAVIDAD ---
        smooth_label = QLabel("⚡ Suavidad de Cámara")
        smooth_label.setStyleSheet("font-weight: bold; font-size: 11px; margin-top: 5px;")
        layout.addWidget(smooth_label)
        
        self.smooth_slider = QSlider(Qt.Orientation.Horizontal)
        self.smooth_slider.setRange(UI_MIN_SUAVIDAD, UI_MAX_SUAVIDAD)
        self.smooth_slider.setValue(
            recording_suavidad_to_ui(self.app_config.user_preferences.recording.suavidad)
        )
        self.smooth_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #e0e0e0;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #2196F3;
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #1976D2;
            }
            QSlider::sub-page:horizontal {
                background: #90caf9;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.smooth_slider)

        # --- AJUSTE DE FPS ---
        fps_label = QLabel("🎥 FPS del Video")
        fps_label.setStyleSheet("font-weight: bold; font-size: 11px; margin-top: 5px;")
        layout.addWidget(fps_label)
        
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(UI_MIN_FPS, UI_MAX_FPS)
        self.fps_spin.setValue(self.app_config.user_preferences.recording.fps)
        self.fps_spin.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                font-size: 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QSpinBox:disabled {
                background: #f5f5f5;
                color: #999;
            }
        """)
        layout.addWidget(self.fps_spin)

        # --- CONTADOR DE TIEMPO (solo visible durante grabación) ---
        self.time_counter = QLabel("00:00:00")
        self.time_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_counter.setStyleSheet("""
            background: #ffebee;
            color: #c62828;
            font-size: 24px;
            font-weight: bold;
            padding: 10px;
            border-radius: 6px;
            font-family: monospace;
        """)
        self.time_counter.setVisible(False)
        layout.addWidget(self.time_counter)
        
        # --- ESTADO ---
        self.status = QLabel("✓ Listo para grabar")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setWordWrap(True)
        self.status.setMinimumHeight(50)
        self.status.setStyleSheet("""
            color: #4caf50;
            font-size: 12px;
            padding: 10px;
            background: #f1f8f4;
            border-radius: 6px;
        """)
        layout.addWidget(self.status)

        # --- PROGRESO ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # --- BOTÓN PRINCIPAL ---
        self.btn = QPushButton("INICIAR GRABACIÓN")
        self.btn.clicked.connect(self.toggle)
        self.btn.setFixedHeight(50)
        self.btn.setStyleSheet("""
            QPushButton {
                background: #4caf50;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #45a049;
            }
            QPushButton:pressed {
                background: #3d8b40;
            }
            QPushButton:disabled {
                background: #cccccc;
            }
        """)
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
    
    def _update_recording_time(self):
        """Actualiza el contador de tiempo durante la grabación."""
        if self.recording_start_time:
            elapsed = time.time() - self.recording_start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.time_counter.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

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
            self.status.setStyleSheet("""
                color: #2e7d32;
                font-size: 11px;
                padding: 10px;
                background: #e8f5e9;
                border-radius: 6px;
            """)

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
                self.status.setStyleSheet("""
                    color: #d32f2f;
                    font-size: 11px;
                    padding: 10px;
                    background: #ffebee;
                    border-radius: 6px;
                """)
                return
            except Exception as exc:
                self.recorder = None
                self._set_controls_enabled(True)
                self.status.setText(f"❌ Error inesperado al iniciar: {exc}")
                self.status.setStyleSheet("""
                    color: #d32f2f;
                    font-size: 11px;
                    padding: 10px;
                    background: #ffebee;
                    border-radius: 6px;
                """)
                return

            # Iniciar el temporizador
            self.recording_start_time = time.time()
            self.timer.start(100)  # Actualizar cada 100ms
            self.time_counter.setVisible(True)
            self.time_counter.setText("00:00:00")
            
            self.btn.setText("DETENER Y PROCESAR")
            self.btn.setStyleSheet("""
                QPushButton {
                    background: #f44336;
                    color: white;
                    font-weight: bold;
                    font-size: 13px;
                    border: none;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background: #d32f2f;
                }
                QPushButton:pressed {
                    background: #b71c1c;
                }
            """)
            
            # Mostrar solo el nombre del archivo, no la ruta completa
            filename = os.path.basename(result.filename)
            self.status.setText(f"● Grabando...\n{filename}")
            self.status.setStyleSheet("""
                color: #d32f2f;
                font-size: 11px;
                padding: 10px;
                background: white;
                border-radius: 6px;
            """)

        else:
            # Detener el temporizador
            self.timer.stop()
            self.time_counter.setVisible(False)
            self.recording_start_time = None
            
            self.btn.setEnabled(False)
            mode = self._get_export_mode()
            label = {"full": "pantalla completa", "tiktok": "TikTok 9:16", "both": "ambos formatos"}[mode]
            self.status.setText(f"⚙️ Renderizando {label}...")
            self.status.setStyleSheet("""
                color: #1976d2;
                font-size: 11px;
                padding: 10px;
                background: #e3f2fd;
                border-radius: 6px;
            """)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            self.render_thread = RenderThread(self.recording_service, self.recorder, export_mode=mode)
            self.render_thread.progress.connect(self.progress_bar.setValue)
            self.render_thread.finished.connect(self.on_finished)
            self.render_thread.start()

    def on_finished(self, full_path, tiktok_path):
        self.btn.setEnabled(True)
        self.btn.setText("INICIAR GRABACIÓN")
        self.btn.setStyleSheet("""
            QPushButton {
                background: #4caf50;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #45a049;
            }
            QPushButton:pressed {
                background: #3d8b40;
            }
        """)

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
        self.status.setStyleSheet("""
            color: #2e7d32;
            font-size: 11px;
            padding: 10px;
            background: #e8f5e9;
            border-radius: 6px;
        """)

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

