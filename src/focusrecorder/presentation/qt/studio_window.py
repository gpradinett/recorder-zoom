import os
import shutil
from pathlib import Path

import cv2
from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QButtonGroup, QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QProgressBar, QPushButton, QRadioButton, QScrollArea, QSlider, QSpinBox, QVBoxLayout, QWidget

from ...application.errors import RecordingEnvironmentError
from ...config.constants import UI_MAX_FPS, UI_MAX_SUAVIDAD, UI_MAX_ZOOM, UI_MIN_FPS, UI_MIN_SUAVIDAD, UI_MIN_ZOOM
from ...infrastructure.audio.sounddevice_audio import HAS_AUDIO
from .recording_presenter import DEFAULT_START_BUTTON_TEXT, RecordingPresenter

if HAS_AUDIO:
    import sounddevice as sd


class FocusApp(QWidget):
    hotkey_stop_requested = pyqtSignal()
    hotkey_pause_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.presenter = RecordingPresenter()
        self.recording_start_time = None
        self.render_thread = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_recording_time)
        self.preview_timer = QTimer()
        self.preview_timer.setInterval(33)
        self.preview_timer.timeout.connect(self._update_preview)
        self._disk_tick = 0
        self.hotkey_stop_requested.connect(self._handle_hotkey_stop)
        self.hotkey_pause_changed.connect(self._handle_hotkey_pause_changed)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Focus Recorder Studio")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumWidth(560)
        self.setMaximumWidth(620)
        self.setObjectName("root")
        self.setStyleSheet(
            "QWidget#root{background:#111827;}QFrame{background:#f8fafc;border:1px solid #d6deeb;border-radius:22px;}"
            "QFrame#hero{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #161b2d,stop:0.55 #1e293b,stop:1 #0f172a);border:1px solid #2f3b55;}"
            "QFrame#previewCard{background:#0b1120;border:1px solid #243044;}QLabel{color:#0f172a;}QLabel#heroTitle{color:white;font-size:28px;font-weight:800;}"
            "QLabel#heroSub{color:#cbd5e1;font-size:12px;}QLabel#badge{background:rgba(255,255,255,.10);color:#e2e8f0;border:1px solid rgba(255,255,255,.10);border-radius:12px;padding:6px 10px;font-size:11px;font-weight:700;}"
            "QLabel#metric{background:rgba(255,255,255,.08);color:white;border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:12px;font-size:11px;}QLabel#time{background:rgba(15,23,42,.45);color:white;border:1px solid rgba(255,255,255,.10);border-radius:16px;padding:10px 14px;font:700 22px Consolas;}"
            "QLabel#section{font-size:16px;font-weight:800;}QLabel#field{color:#334155;font-size:11px;font-weight:800;}QLabel#helper{color:#64748b;font-size:11px;}QLabel#path{background:white;border:1px solid #dbe3ef;border-radius:16px;padding:12px;}"
            "QLabel#preview{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #020617,stop:1 #0f172a);color:#94a3b8;border:1px solid #334155;border-radius:18px;font-size:14px;font-weight:600;}"
            "QLabel#status{padding:16px;border-radius:18px;font-size:13px;font-weight:700;}QLineEdit,QSpinBox,QComboBox{background:white;border:1px solid #dbe3ef;border-radius:16px;padding:10px 12px;font-size:12px;min-height:20px;}QLineEdit:focus,QSpinBox:focus,QComboBox:focus{border:1px solid #f97316;}"
            "QPushButton{border:none;border-radius:16px;padding:12px 16px;font-size:12px;font-weight:800;}QPushButton#ghost{background:white;color:#0f172a;border:1px solid #dbe3ef;}QPushButton#ghost:hover{background:#fff7ed;border:1px solid #fdba74;}"
            "QPushButton#primary{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #ff4141,stop:1 #ff7a18);color:white;font-size:15px;font-weight:900;}QPushButton#primary:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #eb2f2f,stop:1 #f97316);}"
            "QPushButton:disabled{background:#dbe3ef;color:#94a3b8;}QRadioButton{background:white;border:1px solid #dbe3ef;border-radius:18px;padding:14px 12px;font-size:12px;font-weight:800;}QRadioButton:hover{border:1px solid #fdba74;}QRadioButton:checked{background:#fff7ed;border:1px solid #f97316;color:#c2410c;}QRadioButton::indicator{width:0;height:0;}"
            "QCheckBox{font-size:12px;font-weight:700;}QSlider::groove:horizontal{background:#dbe3ef;height:8px;border-radius:4px;}QSlider::sub-page:horizontal{background:#0f766e;border-radius:4px;}QSlider::handle:horizontal{background:white;border:2px solid #0f766e;width:18px;height:18px;margin:-6px 0;border-radius:9px;}QProgressBar{background:#e2e8f0;border:none;border-radius:8px;min-height:10px;}QProgressBar::chunk{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0f766e,stop:1 #22c55e);border-radius:8px;}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        root.addWidget(scroll)

        canvas = QWidget()
        scroll.setWidget(canvas)
        layout = QVBoxLayout(canvas)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)

        ui = self.presenter.get_default_ui_state()

        hero = QFrame()
        hero.setObjectName("hero")
        hero_l = QVBoxLayout(hero)
        top = QHBoxLayout()
        text_l = QVBoxLayout()
        self.header_badge = QLabel("MODO STUDIO")
        self.header_badge.setObjectName("badge")
        text_l.addWidget(self.header_badge, 0, Qt.AlignmentFlag.AlignLeft)
        title = QLabel("Focus Recorder")
        title.setObjectName("heroTitle")
        text_l.addWidget(title)
        sub = QLabel("Grabacion enfocada para cursor, TikTok, pantalla completa o ambas salidas.")
        sub.setWordWrap(True)
        sub.setObjectName("heroSub")
        text_l.addWidget(sub)
        shortcuts = QLabel("F7 pausa o reanuda  |  F10 termina y renderiza  |  la ventana se minimiza al grabar")
        shortcuts.setObjectName("heroSub")
        shortcuts.setWordWrap(True)
        text_l.addWidget(shortcuts)
        top.addLayout(text_l, 1)
        self.time_counter = QLabel("00:00:00")
        self.time_counter.setObjectName("time")
        self.time_counter.setVisible(False)
        top.addWidget(self.time_counter, 0, Qt.AlignmentFlag.AlignTop)
        hero_l.addLayout(top)
        chips = QHBoxLayout()
        self.mode_summary_label = QLabel("Salida\n--")
        self.mode_summary_label.setObjectName("metric")
        self.quality_summary_label = QLabel("Calidad\n--")
        self.quality_summary_label.setObjectName("metric")
        self.disk_label = QLabel("Disco\n--")
        self.disk_label.setObjectName("metric")
        chips.addWidget(self.mode_summary_label)
        chips.addWidget(self.quality_summary_label)
        chips.addWidget(self.disk_label)
        hero_l.addLayout(chips)
        layout.addWidget(hero)

        dest = QFrame()
        dest_l = QVBoxLayout(dest)
        label = QLabel("Destino y nombre")
        label.setObjectName("section")
        dest_l.addWidget(label)
        row = QHBoxLayout()
        self.dir_label = QLabel(self._get_video_directory_display())
        self.dir_label.setObjectName("path")
        self.dir_label.setWordWrap(True)
        row.addWidget(self.dir_label, 1)
        self.change_dir_btn = QPushButton("Cambiar")
        self.change_dir_btn.setObjectName("ghost")
        self.change_dir_btn.clicked.connect(self._change_output_directory)
        row.addWidget(self.change_dir_btn)
        dest_l.addLayout(row)
        name_label = QLabel("Nombre del video")
        name_label.setObjectName("field")
        dest_l.addWidget(name_label)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: tutorial_demo  |  vacio = automatico")
        dest_l.addWidget(self.name_input)
        layout.addWidget(dest)

        record = QFrame()
        record_l = QVBoxLayout(record)
        sec = QLabel("Formato y camara")
        sec.setObjectName("section")
        record_l.addWidget(sec)
        self.export_group = QButtonGroup(self)
        mode_row = QHBoxLayout()
        self.radio_full = QRadioButton("16:9\nPantalla completa")
        self.radio_tiktok = QRadioButton("9:16\nTikTok vertical")
        self.radio_both = QRadioButton("Dual\nAmbos formatos")
        self.export_group.addButton(self.radio_full, 0)
        self.export_group.addButton(self.radio_tiktok, 1)
        self.export_group.addButton(self.radio_both, 2)
        self.export_group.buttonClicked.connect(self._update_mode_summary)
        if ui["export_mode"] == "full":
            self.radio_full.setChecked(True)
        elif ui["export_mode"] == "tiktok":
            self.radio_tiktok.setChecked(True)
        else:
            self.radio_both.setChecked(True)
        mode_row.addWidget(self.radio_full)
        mode_row.addWidget(self.radio_tiktok)
        mode_row.addWidget(self.radio_both)
        record_l.addLayout(mode_row)
        grid = QGridLayout()
        for text, col in (("Zoom", 0), ("Suavidad", 1), ("FPS", 2)):
            field = QLabel(text)
            field.setObjectName("field")
            grid.addWidget(field, 0, col)
        self.zoom_spin = QSpinBox()
        self.zoom_spin.setRange(UI_MIN_ZOOM, UI_MAX_ZOOM)
        self.zoom_spin.setValue(ui["zoom"])
        self.zoom_spin.setPrefix("x ")
        self.zoom_spin.setSingleStep(2)
        self.zoom_spin.valueChanged.connect(self._update_mode_summary)
        grid.addWidget(self.zoom_spin, 1, 0)
        self.smooth_slider = QSlider(Qt.Orientation.Horizontal)
        self.smooth_slider.setRange(UI_MIN_SUAVIDAD, UI_MAX_SUAVIDAD)
        self.smooth_slider.setValue(ui["suavidad"])
        self.smooth_slider.valueChanged.connect(self._update_mode_summary)
        grid.addWidget(self.smooth_slider, 1, 1)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(UI_MIN_FPS, UI_MAX_FPS)
        self.fps_spin.setValue(ui["fps"])
        self.fps_spin.valueChanged.connect(self._update_mode_summary)
        grid.addWidget(self.fps_spin, 1, 2)
        self.smooth_value_label = QLabel()
        self.smooth_value_label.setObjectName("helper")
        grid.addWidget(self.smooth_value_label, 2, 1)
        self.preview_quality_label = QLabel()
        self.preview_quality_label.setObjectName("helper")
        grid.addWidget(self.preview_quality_label, 2, 2)
        record_l.addLayout(grid)
        layout.addWidget(record)

        audio = QFrame()
        audio_l = QVBoxLayout(audio)
        sec = QLabel("Audio")
        sec.setObjectName("section")
        audio_l.addWidget(sec)
        self.audio_checkbox = QCheckBox("Capturar microfono")
        self.audio_checkbox.setEnabled(HAS_AUDIO)
        if not HAS_AUDIO:
            self.audio_checkbox.setText("Capturar microfono (instala sounddevice)")
        self.audio_checkbox.setChecked(ui["audio"])
        self.audio_checkbox.toggled.connect(self._handle_audio_toggle)
        audio_l.addWidget(self.audio_checkbox)
        self.audio_device_combo = QComboBox()
        self.audio_device_combo.setVisible(False)
        if HAS_AUDIO:
            self.audio_device_combo.addItem("Dispositivo por defecto", None)
            try:
                for index, device in enumerate(sd.query_devices()):
                    if device["max_input_channels"] > 0:
                        self.audio_device_combo.addItem(device["name"], index)
            except Exception:
                pass
        audio_l.addWidget(self.audio_device_combo)
        self.vu_meter = QProgressBar()
        self.vu_meter.setRange(0, 100)
        self.vu_meter.setValue(0)
        self.vu_meter.setTextVisible(False)
        self.vu_meter.setFixedHeight(12)
        self.vu_meter.setVisible(False)
        audio_l.addWidget(self.vu_meter)
        tip = QLabel("Activa microfono solo si necesitas voz para tutoriales.")
        tip.setObjectName("helper")
        tip.setWordWrap(True)
        audio_l.addWidget(tip)
        layout.addWidget(audio)
        self._handle_audio_toggle(ui["audio"])

        preview = QFrame()
        preview.setObjectName("previewCard")
        preview_l = QVBoxLayout(preview)
        sec = QLabel("Vista previa")
        sec.setObjectName("section")
        sec.setStyleSheet("color:white;")
        preview_l.addWidget(sec)
        self.preview_label = QLabel("Sin senal")
        self.preview_label.setObjectName("preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(260)
        preview_l.addWidget(self.preview_label)
        foot = QHBoxLayout()
        self.preview_hint_label = QLabel("Preview nitido y suavizado dentro de la ventana.")
        self.preview_hint_label.setObjectName("helper")
        self.preview_hint_label.setStyleSheet("color:#cbd5e1;")
        foot.addWidget(self.preview_hint_label, 1)
        self.preview_mode_label = QLabel("--")
        self.preview_mode_label.setObjectName("badge")
        foot.addWidget(self.preview_mode_label, 0, Qt.AlignmentFlag.AlignRight)
        preview_l.addLayout(foot)
        layout.addWidget(preview)

        status_card = QFrame()
        status_l = QVBoxLayout(status_card)
        sec = QLabel("Estado")
        sec.setObjectName("section")
        status_l.addWidget(sec)
        self.status = QLabel()
        self.status.setObjectName("status")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setWordWrap(True)
        status_l.addWidget(self.status)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_l.addWidget(self.progress_bar)
        layout.addWidget(status_card)

        actions = QFrame()
        actions_l = QVBoxLayout(actions)
        tools = QHBoxLayout()
        self.open_folder_btn = QPushButton("Abrir carpeta")
        self.open_folder_btn.setObjectName("ghost")
        self.open_folder_btn.clicked.connect(self.presenter.reveal_output_directory)
        tools.addWidget(self.open_folder_btn)
        self.open_last_btn = QPushButton("Mostrar ultimo")
        self.open_last_btn.setObjectName("ghost")
        self.open_last_btn.setEnabled(False)
        self.open_last_btn.clicked.connect(self.presenter.reveal_last_export)
        tools.addWidget(self.open_last_btn)
        self.play_last_btn = QPushButton("Reproducir")
        self.play_last_btn.setObjectName("ghost")
        self.play_last_btn.setEnabled(False)
        self.play_last_btn.clicked.connect(self._play_last_export)
        tools.addWidget(self.play_last_btn)
        actions_l.addLayout(tools)
        self.btn = QPushButton(DEFAULT_START_BUTTON_TEXT)
        self.btn.setObjectName("primary")
        self.btn.setFixedHeight(56)
        self.btn.clicked.connect(self.toggle)
        actions_l.addWidget(self.btn)
        layout.addWidget(actions)

        self._update_mode_summary()
        self._update_disk_info()
        self._update_status_text("Listo para grabar", self._success_status_style())
        self._center_on_screen()

    def _get_video_directory_display(self):
        return self.presenter.get_output_dir_display()

    def _get_export_mode(self):
        return {0: "full", 1: "tiktok", 2: "both"}[self.export_group.checkedId()]

    def _set_controls_enabled(self, enabled):
        for widget in (self.zoom_spin, self.smooth_slider, self.fps_spin, self.radio_full, self.radio_tiktok, self.radio_both, self.change_dir_btn, self.name_input, self.audio_checkbox, self.audio_device_combo):
            widget.setEnabled(enabled)

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = self.frameGeometry()
            geo.moveCenter(screen.availableGeometry().center())
            self.move(geo.topLeft())

    def _handle_audio_toggle(self, checked):
        self.audio_device_combo.setVisible(checked and HAS_AUDIO)
        self.vu_meter.setVisible(checked and self.presenter.has_active_recording())

    def _update_status_text(self, text, style):
        self.status.setText(text)
        self.status.setStyleSheet(style)

    def _update_mode_summary(self):
        mode = self._get_export_mode()
        label = {"full": "16:9 full", "tiktok": "9:16 vertical", "both": "Full + TikTok"}[mode]
        self.mode_summary_label.setText(f"Salida\n{label}")
        self.quality_summary_label.setText(f"Calidad\n{self.fps_spin.value()} FPS | x{self.zoom_spin.value() / 10:.1f}")
        self.smooth_value_label.setText(f"Seguimiento suave: {self.smooth_slider.value()} / {UI_MAX_SUAVIDAD}")
        self.preview_quality_label.setText(f"Vista fluida con {self.fps_spin.value()} FPS.")
        self.preview_mode_label.setText(label)

    def _update_recording_time(self):
        recorder = self.presenter.recorder
        if recorder is not None and recorder.is_recording:
            elapsed = recorder.get_elapsed_time()
            self.time_counter.setText(f"{int(elapsed // 3600):02d}:{int((elapsed % 3600) // 60):02d}:{int(elapsed % 60):02d}")

    def _change_output_directory(self):
        current_dir = self.presenter.get_output_dir_display()
        new_dir = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de destino para videos", current_dir, QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks)
        if new_dir:
            self.presenter.update_output_directory(Path(new_dir))
            self.dir_label.setText(self.presenter.get_output_dir_display())
            self._update_status_text(f"Carpeta actualizada\n{Path(new_dir).name}", self._success_status_style())
            self._update_disk_info()

    def toggle(self):
        if not self.presenter.has_active_recording():
            self._set_controls_enabled(False)
            try:
                view_model = self.presenter.start_recording(zoom=self.zoom_spin.value(), suavidad=self.smooth_slider.value(), fps=self.fps_spin.value(), custom_name=self.name_input.text().strip(), audio=self.audio_checkbox.isChecked(), audio_device=self.audio_device_combo.currentData() if self.audio_checkbox.isChecked() else None)
            except RecordingEnvironmentError as exc:
                self._set_controls_enabled(True)
                self._update_status_text(f"Error al iniciar\n{exc}", self._error_status_style())
                return
            except Exception as exc:
                self._set_controls_enabled(True)
                self._update_status_text(f"Error inesperado\n{exc}", self._error_status_style())
                return
            self.recording_start_time = True
            self.timer.start(100)
            self.preview_timer.start()
            self.time_counter.setVisible(True)
            self.vu_meter.setVisible(self.audio_checkbox.isChecked())
            self.btn.setText(view_model.button_text)
            self.btn.setStyleSheet(self._stop_button_style())
            self.presenter.recorder.on_pause_toggled = self.hotkey_pause_changed.emit
            self.presenter.recorder.on_stop_requested = self.hotkey_stop_requested.emit
            self.header_badge.setText("REC EN CURSO")
            self._update_status_text(f"{view_model.status_text}\nF7 pausa o reanuda  |  F10 termina", self._recording_status_style())
            self.showMinimized()
            return

        self.timer.stop()
        self.preview_timer.stop()
        self.vu_meter.setVisible(False)
        self.preview_label.clear()
        self.preview_label.setText("Procesando video...")
        self.time_counter.setVisible(False)
        self.recording_start_time = None
        self.btn.setEnabled(False)
        mode = self._get_export_mode()
        self.presenter.save_current_preferences(zoom=self.zoom_spin.value(), suavidad=self.smooth_slider.value(), fps=self.fps_spin.value(), export_mode=mode)
        render_view_model = self.presenter.build_rendering_view_model(mode)
        self._update_status_text(render_view_model.status_text, self._rendering_status_style())
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.header_badge.setText("RENDERIZANDO")
        from . import main_window as main_window_module

        self.render_thread = main_window_module.RenderThread(self.presenter, export_mode=mode)
        self.render_thread.progress.connect(self.progress_bar.setValue)
        self.render_thread.finished.connect(self.on_finished)
        self.render_thread.start()

    def on_finished(self, result):
        self.timer.stop()
        self.preview_timer.stop()
        self.time_counter.setVisible(False)
        self.recording_start_time = None
        self.btn.setEnabled(True)
        view_model = self.presenter.build_finished_view_model(result)
        self.btn.setText(view_model.button_text)
        self.btn.setStyleSheet(self._start_button_style())
        self._update_status_text(view_model.status_text, self._success_status_style())
        self.progress_bar.setVisible(False)
        self.preview_label.clear()
        self.preview_label.setText("Sin senal")
        self.header_badge.setText("LISTO")
        self.preview_hint_label.setText("Preview nitido y suavizado dentro de la ventana.")
        self._set_controls_enabled(True)
        self._update_disk_info()
        has_output = bool(view_model.primary_path)
        self.open_last_btn.setEnabled(has_output)
        self.play_last_btn.setEnabled(has_output)
        self.presenter.reveal_output_directory()

    def _handle_hotkey_stop(self):
        if self.presenter.has_active_recording() and self.btn.isEnabled():
            self.showNormal()
            self.raise_()
            self.activateWindow()
            self.toggle()

    def _handle_hotkey_pause_changed(self, paused):
        if paused:
            self.header_badge.setText("PAUSADO")
            self._update_status_text("Grabacion en pausa\nF7 reanuda  |  F10 termina", self._rendering_status_style())
            self.preview_hint_label.setText("Captura pausada. El ultimo frame queda congelado.")
        else:
            self.header_badge.setText("REC EN CURSO")
            self._update_status_text("Grabando ahora\nF7 pausa o reanuda  |  F10 termina", self._recording_status_style())
            self.preview_hint_label.setText("Preview nitido y suavizado dentro de la ventana.")

    def _update_preview(self):
        recorder = self.presenter.recorder
        if recorder is None:
            return
        mode = self._get_export_mode()
        frame = recorder.preview_frame_tiktok if mode == "tiktok" else recorder.preview_frame
        if frame is not None:
            height, width, channels = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = QImage(rgb.data, width, height, width * channels, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(image).scaled(self.preview_label.width(), self.preview_label.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_label.setPixmap(pixmap)
        if self.audio_checkbox.isChecked():
            self.vu_meter.setValue(recorder.audio_level)
        self._disk_tick += 1
        if self._disk_tick >= 15:
            self._disk_tick = 0
            self._update_disk_info()

    def _update_disk_info(self):
        output_dir = self.presenter.get_output_dir_display()
        drive = os.path.splitdrive(output_dir)[0] or "/"
        try:
            free_gb = shutil.disk_usage(drive).free / 1024 ** 3
        except OSError:
            free_gb = 0.0
        temp_mb = 0.0
        recorder = self.presenter.recorder
        if recorder is not None and recorder._temp_path:
            try:
                temp_mb = os.path.getsize(recorder._temp_path) / 1024 ** 2
            except OSError:
                pass
        self.disk_label.setText(f"Disco\n{free_gb:.1f} GB libres" if temp_mb <= 0 else f"Disco\n{free_gb:.1f} GB libres | temp {temp_mb:.0f} MB")

    def _play_last_export(self):
        target = self.presenter.get_last_export_path()
        if target:
            QDesktopServices.openUrl(QUrl.fromLocalFile(target))

    @staticmethod
    def _start_button_style():
        return ""

    @staticmethod
    def _stop_button_style():
        return "QPushButton#primary{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #b91c1c,stop:1 #ef4444);color:white;font-size:14px;font-weight:800;}QPushButton#primary:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #991b1b,stop:1 #dc2626);}"

    @staticmethod
    def _error_status_style():
        return "color:#7f1d1d;background:#fee2e2;border:1px solid #fecaca;"

    @staticmethod
    def _recording_status_style():
        return "color:#7f1d1d;background:#fff1f2;border:1px solid #fecdd3;"

    @staticmethod
    def _rendering_status_style():
        return "color:#1d4ed8;background:#dbeafe;border:1px solid #bfdbfe;"

    @staticmethod
    def _success_status_style():
        return "color:#166534;background:#dcfce7;border:1px solid #bbf7d0;"
