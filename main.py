import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QSlider, QSpinBox, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from recorder import FocusRecorder

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

class RenderThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, recorder):
        super().__init__()
        self.recorder = recorder

    def run(self):
        self.recorder.stop(callback_progress=self.progress.emit)
        self.finished.emit()

class FocusApp(QWidget):
    def __init__(self):
        super().__init__()
        self.recorder = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("FocusSee Control Panel")
        self.setFixedWidth(300)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout()

        # --- AJUSTE DE ZOOM ---
        layout.addWidget(QLabel("Nivel de Zoom:"))
        self.zoom_spin = QSpinBox()
        self.zoom_spin.setRange(10, 40) # Representa 1.0 a 4.0
        self.zoom_spin.setValue(18)
        self.zoom_spin.setPrefix("x ")
        self.zoom_spin.setSingleStep(2)
        layout.addWidget(self.zoom_spin)

        # --- AJUSTE DE SUAVIDAD ---
        layout.addWidget(QLabel("Suavidad de Cámara (Inercia):"))
        self.smooth_slider = QSlider(Qt.Orientation.Horizontal)
        self.smooth_slider.setRange(1, 20)
        self.smooth_slider.setValue(5) # 0.05
        layout.addWidget(self.smooth_slider)

        # --- AJUSTE DE FPS ---
        layout.addWidget(QLabel("FPS del Video Final:"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(24, 60)
        self.fps_spin.setValue(60)
        layout.addWidget(self.fps_spin)

        # --- ESTADO Y PROGRESO ---
        self.status = QLabel("Listo")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # --- BOTÓN PRINCIPAL ---
        self.btn = QPushButton("INICIAR GRABACIÓN")
        self.btn.clicked.connect(self.toggle)
        self.btn.setStyleSheet("height: 50px; background: #28a745; color: white; font-weight: bold;")
        layout.addWidget(self.btn)

        self.setLayout(layout)

    def get_config(self):
        return {
            'zoom': self.zoom_spin.value() / 10.0,
            'suavidad': self.smooth_slider.value() / 100.0,
            'fps': self.fps_spin.value()
        }

    def toggle(self):
        if self.recorder is None or not self.recorder.is_recording:
            # Bloquear UI mientras graba
            self.zoom_spin.setEnabled(False)
            self.smooth_slider.setEnabled(False)
            self.fps_spin.setEnabled(False)
            
            self.recorder = FocusRecorder(config=self.get_config())
            self.recorder.start()
            self.btn.setText("DETENER Y PROCESAR")
            self.btn.setStyleSheet("background: #dc3545; color: white;")
            self.status.setText("🔴 Grabando...")
        else:
            self.btn.setEnabled(False)
            self.status.setText("⚙️ Renderizando video...")
            self.progress_bar.setVisible(True)
            
            # Usamos un hilo para no congelar la ventana al renderizar
            self.render_thread = RenderThread(self.recorder)
            self.render_thread.progress.connect(self.progress_bar.setValue)
            self.render_thread.finished.connect(self.on_finished)
            self.render_thread.start()

    def on_finished(self):
        self.btn.setEnabled(True)
        self.btn.setText("INICIAR GRABACIÓN")
        self.btn.setStyleSheet("background: #28a745; color: white;")
        self.status.setText("✅ Video Guardado")
        self.progress_bar.setVisible(False)
        self.zoom_spin.setEnabled(True)
        self.smooth_slider.setEnabled(True)
        self.fps_spin.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = FocusApp()
    ex.show()
    sys.exit(app.exec())