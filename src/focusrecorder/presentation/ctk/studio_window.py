import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
import cv2
from PIL import Image, ImageTk

from ...application.errors import RecordingEnvironmentError
from ...config.constants import UI_DEFAULT_ZOOM, UI_MAX_FPS, UI_MAX_SUAVIDAD, UI_MAX_ZOOM, UI_MIN_FPS, UI_MIN_SUAVIDAD, UI_MIN_ZOOM
from ...infrastructure.audio.sounddevice_audio import (
    HAS_AUDIO,
    list_microphone_devices,
    list_system_audio_devices,
)
from ..qt.recording_presenter import RecordingPresenter

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

START_TEXT = "INICIAR GRABACION"
STOP_TEXT = "DETENER Y PROCESAR"


class FocusApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.presenter = RecordingPresenter()
        self.render_thread = None
        self.preview_job = None
        self.clock_job = None
        self.preview_image = None
        self.audio_devices = {"mic": {"Dispositivo por defecto": None}, "system": {}}
        self.audio_source_var = tk.StringVar(value="Microfono")
        self.preview_enabled_var = tk.BooleanVar(value=True)
        self.pause_hotkey_var = tk.StringVar(value="F7")
        self.stop_hotkey_var = tk.StringVar(value="F10")
        self.quality_var = tk.StringVar(value="Alta")
        self._hotkey_capture_target = None
        self._disk_tick = 0
        self._build_window()
        self._build_layout()
        self._load_initial_state()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_window(self):
        self.title("Focus Recorder Studio")
        self.geometry("1120x740")
        self.minsize(1020, 680)
        self.configure(fg_color="#0b1020")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _make_card(self, parent, title):
        card = ctk.CTkFrame(parent, fg_color="#10182b", corner_radius=24, border_width=1, border_color="#24314f")
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card, text=title, text_color="#f8fafc", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 14))
        return card

    def _field_title(self, parent, text):
        return ctk.CTkLabel(parent, text=text, text_color="#d6e1fb", font=ctk.CTkFont(size=13, weight="bold"))

    def _pill(self, parent, text):
        return ctk.CTkLabel(parent, text=text, fg_color="#172036", corner_radius=999, text_color="#dce7ff", padx=12, pady=6, font=ctk.CTkFont(size=12, weight="bold"))

    def _tool_button(self, parent, text, command):
        return ctk.CTkButton(parent, text=text, command=command, height=44, corner_radius=14, fg_color="#172036", hover_color="#223150", border_width=1, border_color="#2c3d61", text_color="#f8fafc", font=ctk.CTkFont(size=13, weight="bold"))

    def _metric(self, title, value):
        frame = ctk.CTkFrame(self.sidebar, fg_color="#18233f", corner_radius=18, border_width=1, border_color="#233354")
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text=title, anchor="w", text_color="#8ea0c8", font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 2))
        frame.value_label = ctk.CTkLabel(frame, text=value, anchor="w", text_color="#ffffff", font=ctk.CTkFont(size=15, weight="bold"))
        frame.value_label.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 12))
        return frame

    def _build_layout(self):
        shell = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=0)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.grid_columnconfigure(1, weight=1)
        shell.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(shell, width=280, fg_color="#131c31", corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)
        self._build_sidebar()

        content = ctk.CTkFrame(shell, fg_color="#0b1020", corner_radius=0)
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        self.header = ctk.CTkFrame(content, fg_color="#0b1020", corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 12))
        self.header.grid_columnconfigure(0, weight=1)
        self._build_header()

        self.body = ctk.CTkScrollableFrame(content, fg_color="#0b1020", corner_radius=0, scrollbar_button_color="#1f2a44", scrollbar_button_hover_color="#2f3e63")
        self.body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))
        self.body.grid_columnconfigure((0, 1), weight=1, uniform="body")
        self._build_cards()

    def _build_sidebar(self):
        self.sidebar.grid_rowconfigure(8, weight=1)
        ctk.CTkLabel(self.sidebar, text="REC", width=46, height=46, corner_radius=14, fg_color="#ff6b2c", text_color="white", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=24, pady=(28, 10), sticky="w")
        ctk.CTkLabel(self.sidebar, text="Focus Recorder", text_color="#f8fafc", font=ctk.CTkFont(size=28, weight="bold")).grid(row=1, column=0, padx=24, sticky="w")
        ctk.CTkLabel(self.sidebar, text="Studio de grabacion para cursor, vertical, full screen y render dual.", justify="left", wraplength=220, text_color="#8ea0c8", font=ctk.CTkFont(size=13)).grid(row=2, column=0, padx=24, pady=(8, 18), sticky="w")
        self.header_badge = ctk.CTkLabel(self.sidebar, text="LISTO", fg_color="#18233f", corner_radius=999, text_color="#d7e3ff", font=ctk.CTkFont(size=12, weight="bold"), padx=16, pady=8)
        self.header_badge.grid(row=3, column=0, padx=24, sticky="w")
        self.time_counter = ctk.CTkLabel(self.sidebar, text="00:00:00", text_color="#ffffff", font=ctk.CTkFont(size=34, weight="bold"))
        self.time_counter.grid(row=4, column=0, padx=24, pady=(18, 6), sticky="w")
        self.hotkeys_label = ctk.CTkLabel(self.sidebar, text="", justify="left", text_color="#8ea0c8", font=ctk.CTkFont(size=12))
        self.hotkeys_label.grid(row=5, column=0, padx=24, pady=(0, 18), sticky="w")
        self.metric_mode = self._metric("Salida", "--"); self.metric_mode.grid(row=6, column=0, padx=24, pady=(0, 10), sticky="ew")
        self.metric_quality = self._metric("Calidad", "--"); self.metric_quality.grid(row=7, column=0, padx=24, pady=(0, 10), sticky="ew")
        self.metric_disk = self._metric("Disco", "--"); self.metric_disk.grid(row=9, column=0, padx=24, pady=(0, 24), sticky="ew")

    def _build_header(self):
        ctk.CTkLabel(self.header, text="Sistema de captura", text_color="#f8fafc", font=ctk.CTkFont(size=30, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(self.header, text="Enfocado a la grabación del cursor + seguimiento", text_color="#8ea0c8", font=ctk.CTkFont(size=13)).grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.window_mode_tag = ctk.CTkLabel(self.header, text="Cursor-first Studio", fg_color="#172036", corner_radius=999, text_color="#dce7ff", padx=18, pady=10, font=ctk.CTkFont(size=13, weight="bold"))
        self.window_mode_tag.grid(row=0, column=1, rowspan=2, sticky="e")

    def _build_cards(self):
        self.dest_card = self._make_card(self.body, "Destino y nombre"); self.dest_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=(0, 12))
        self.mode_card = self._make_card(self.body, "Formato y enfoque"); self.mode_card.grid(row=0, column=1, sticky="nsew", padx=(12, 0), pady=(0, 12))
        self.preview_card = self._make_card(self.body, "Vista previa"); self.preview_card.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 12))
        self.audio_card = self._make_card(self.body, "Audio"); self.audio_card.grid(row=2, column=0, sticky="nsew", padx=(0, 12), pady=(0, 12))
        self.status_card = self._make_card(self.body, "Estado"); self.status_card.grid(row=2, column=1, sticky="nsew", padx=(12, 0), pady=(0, 12))
        self.actions_card = self._make_card(self.body, "Acciones"); self.actions_card.grid(row=3, column=0, columnspan=2, sticky="nsew")
        self._build_destination_card(self.dest_card)
        self._build_mode_card(self.mode_card)
        self._build_preview_card(self.preview_card)
        self._build_audio_card(self.audio_card)
        self._build_status_card(self.status_card)
        self._build_actions_card(self.actions_card)

    def _build_destination_card(self, card):
        self.dir_label = ctk.CTkLabel(card, text="", justify="left", anchor="w", text_color="#e7edf9", fg_color="#111827", corner_radius=16, height=70, wraplength=420, padx=16)
        self.dir_label.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))
        self.change_dir_btn = ctk.CTkButton(card, text="Elegir carpeta", command=self._change_output_directory, height=42, corner_radius=14, fg_color="#24314f", hover_color="#314468")
        self.change_dir_btn.grid(row=1, column=1, sticky="e", padx=(0, 18), pady=(0, 12))
        self._field_title(card, "Nombre del video").grid(row=2, column=0, columnspan=2, sticky="w", padx=18)
        self.name_input = ctk.CTkEntry(card, placeholder_text="Ej: tutorial_tiktok, demo_producto, clase_cursor", height=44, corner_radius=14, border_width=1, fg_color="#0f172a", border_color="#2a3a59")
        self.name_input.grid(row=3, column=0, columnspan=2, sticky="ew", padx=18, pady=(8, 18))

    def _build_mode_card(self, card):
        self.export_mode_var = tk.StringVar(value="Pantalla")
        self.mode_selector = ctk.CTkSegmentedButton(card, values=["Pantalla", "TikTok", "Ambos"], variable=self.export_mode_var, command=lambda _v: self._update_mode_summary(), height=42, corner_radius=14, selected_color="#ff6b2c", selected_hover_color="#ff5a14", unselected_color="#172036", unselected_hover_color="#202b45")
        self.mode_selector.grid(row=1, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 16))
        self.radio_full = self.mode_selector; self.radio_tiktok = self.mode_selector; self.radio_both = self.mode_selector
        self._field_title(card, "Zoom").grid(row=2, column=0, sticky="w", padx=18); self.zoom_value_label = self._pill(card, ""); self.zoom_value_label.grid(row=2, column=1, sticky="e", padx=18)
        self.zoom_spin = ctk.CTkSlider(card, from_=UI_MIN_ZOOM, to=UI_MAX_ZOOM, number_of_steps=UI_MAX_ZOOM - UI_MIN_ZOOM, command=lambda _v: self._update_mode_summary(), progress_color="#1f8a70", button_color="#f8fafc", button_hover_color="#ffffff")
        self.zoom_spin.grid(row=3, column=0, columnspan=2, sticky="ew", padx=18, pady=(8, 12))
        self._field_title(card, "Suavidad").grid(row=4, column=0, sticky="w", padx=18); self.smooth_value_label = self._pill(card, ""); self.smooth_value_label.grid(row=4, column=1, sticky="e", padx=18)
        self.smooth_slider = ctk.CTkSlider(card, from_=UI_MIN_SUAVIDAD, to=UI_MAX_SUAVIDAD, number_of_steps=UI_MAX_SUAVIDAD - UI_MIN_SUAVIDAD, command=lambda _v: self._update_mode_summary(), progress_color="#1f8a70", button_color="#f8fafc", button_hover_color="#ffffff")
        self.smooth_slider.grid(row=5, column=0, columnspan=2, sticky="ew", padx=18, pady=(8, 12))
        self._field_title(card, "FPS").grid(row=6, column=0, sticky="w", padx=18); self.fps_value_label = self._pill(card, ""); self.fps_value_label.grid(row=6, column=1, sticky="e", padx=18)
        self.fps_spin = ctk.CTkSlider(card, from_=UI_MIN_FPS, to=UI_MAX_FPS, number_of_steps=UI_MAX_FPS - UI_MIN_FPS, command=lambda _v: self._update_mode_summary(), progress_color="#1f8a70", button_color="#f8fafc", button_hover_color="#ffffff")
        self.fps_spin.grid(row=7, column=0, columnspan=2, sticky="ew", padx=18, pady=(8, 8))
        self.preview_quality_label = ctk.CTkLabel(card, text="", text_color="#8ea0c8", justify="left", font=ctk.CTkFont(size=12))
        self.preview_quality_label.grid(row=8, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 18))
        self._field_title(card, "Calidad").grid(row=9, column=0, sticky="w", padx=18, pady=(0, 8))
        self.quality_selector = ctk.CTkSegmentedButton(card, values=["Baja", "Media", "Alta", "Muy alta"], variable=self.quality_var, command=lambda _v: self._update_mode_summary(), height=38, corner_radius=12, selected_color="#ff6b2c", selected_hover_color="#ff5a14", unselected_color="#172036", unselected_hover_color="#202b45")
        self.quality_selector.grid(row=10, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 18))
        self._field_title(card, "Pausa").grid(row=11, column=0, sticky="w", padx=18, pady=(0, 8))
        self._field_title(card, "Detener").grid(row=11, column=1, sticky="w", padx=18, pady=(0, 8))
        self.pause_hotkey_button = ctk.CTkButton(card, textvariable=self.pause_hotkey_var, command=lambda: self._start_hotkey_capture("pause"), height=38, corner_radius=12, fg_color="#0f172a", hover_color="#16213a", border_width=1, border_color="#2a3a59", text_color="#f8fafc")
        self.pause_hotkey_button.grid(row=12, column=0, sticky="ew", padx=18, pady=(0, 8))
        self.stop_hotkey_button = ctk.CTkButton(card, textvariable=self.stop_hotkey_var, command=lambda: self._start_hotkey_capture("stop"), height=38, corner_radius=12, fg_color="#0f172a", hover_color="#16213a", border_width=1, border_color="#2a3a59", text_color="#f8fafc")
        self.stop_hotkey_button.grid(row=12, column=1, sticky="ew", padx=18, pady=(0, 8))
        self.hotkey_capture_hint = ctk.CTkLabel(card, text="Haz click y presiona una tecla F para asignarla.", text_color="#8ea0c8", justify="left", font=ctk.CTkFont(size=12))
        self.hotkey_capture_hint.grid(row=13, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 18))

    def _build_preview_card(self, card):
        card.grid_columnconfigure(0, weight=1)
        controls = ctk.CTkFrame(card, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 10))
        controls.grid_columnconfigure(0, weight=1)
        self.preview_toggle = ctk.CTkSwitch(controls, text="Previsualizacion", variable=self.preview_enabled_var, command=self._handle_preview_toggle, progress_color="#ff6b2c", button_color="#ffffff", button_hover_color="#f8fafc")
        self.preview_toggle.grid(row=0, column=1, sticky="e")
        self.preview_canvas = tk.Label(card, text="Sin señal", bg="#050b16", fg="#c5d2ee", font=("Segoe UI", 18, "bold"), relief="flat")
        self.preview_canvas.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 12))
        self.preview_canvas.configure(height=12)
        footer = ctk.CTkFrame(card, fg_color="transparent"); footer.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 18)); footer.grid_columnconfigure(0, weight=1)
        self.preview_hint_label = ctk.CTkLabel(footer, text="Preview fluido dentro de la app y render final con cursor visible.", text_color="#8ea0c8", font=ctk.CTkFont(size=12))
        self.preview_hint_label.grid(row=0, column=0, sticky="w")
        self.preview_mode_label = ctk.CTkLabel(footer, text="--", fg_color="#172036", corner_radius=999, text_color="#dce7ff", padx=14, pady=8, font=ctk.CTkFont(size=12, weight="bold"))
        self.preview_mode_label.grid(row=0, column=1, sticky="e")

    def _build_audio_card(self, card):
        self.audio_checkbox = ctk.CTkCheckBox(card, text="Capturar micrófono", command=self._handle_audio_toggle, checkbox_width=22, checkbox_height=22, corner_radius=6, fg_color="#ff6b2c", hover_color="#ff5a14", text_color="#edf3ff")
        self.audio_checkbox.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 14))
        self.audio_source_selector = ctk.CTkSegmentedButton(card, values=["Microfono", "Escritorio", "Ambos"], variable=self.audio_source_var, command=lambda _value: self._load_audio_devices(), height=36, corner_radius=12, selected_color="#ff6b2c", selected_hover_color="#ff5a14", unselected_color="#172036", unselected_hover_color="#202b45")
        self.audio_source_selector.grid(row=5, column=0, sticky="ew", padx=18, pady=(0, 18))
        self.audio_device_combo = ctk.CTkComboBox(card, values=["Dispositivo por defecto"], state="readonly", height=42, corner_radius=14, fg_color="#0f172a", border_color="#2a3a59", button_color="#24314f", button_hover_color="#314468", dropdown_fg_color="#0f172a")
        self.audio_device_combo.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 14))
        self.vu_meter = ctk.CTkProgressBar(card, progress_color="#22c55e", fg_color="#182238", height=12)
        self.vu_meter.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 14)); self.vu_meter.set(0)
        ctk.CTkLabel(card, text="Activa micrófono solo si necesitas voz encima de la grabación.", text_color="#8ea0c8", justify="left", font=ctk.CTkFont(size=12)).grid(row=4, column=0, sticky="w", padx=18, pady=(0, 18))

    def _build_status_card(self, card):
        self.status = ctk.CTkLabel(card, text="", justify="left", anchor="w", text_color="#0f172a", fg_color="#d9fbe6", corner_radius=16, height=132, wraplength=420, padx=18, pady=18, font=ctk.CTkFont(size=15, weight="bold"))
        self.status.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 14))
        self.progress_bar = ctk.CTkProgressBar(card, progress_color="#ff6b2c", fg_color="#1a2236", height=12)
        self.progress_bar.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 10)); self.progress_bar.set(0)
        self.progress_hint = ctk.CTkLabel(card, text="El progreso aparece aquí cuando termina la captura y comienza el render.", text_color="#8ea0c8", justify="left", font=ctk.CTkFont(size=12))
        self.progress_hint.grid(row=3, column=0, sticky="w", padx=18, pady=(0, 18))

    def _build_actions_card(self, card):
        tools = ctk.CTkFrame(card, fg_color="transparent"); tools.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 16)); tools.grid_columnconfigure((0, 1, 2), weight=1)
        self.open_folder_btn = self._tool_button(tools, "Abrir carpeta", self._open_output_folder); self.open_folder_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.open_last_btn = self._tool_button(tools, "Mostrar último", self.presenter.reveal_last_export); self.open_last_btn.grid(row=0, column=1, sticky="ew", padx=8)
        self.play_last_btn = self._tool_button(tools, "Reproducir", self._play_last_export); self.play_last_btn.grid(row=0, column=2, sticky="ew", padx=(8, 0))
        self.btn = ctk.CTkButton(card, text=START_TEXT, command=self.toggle, height=60, corner_radius=18, fg_color="#ff6b2c", hover_color="#ff5a14", text_color="white", font=ctk.CTkFont(size=18, weight="bold"))
        self.btn.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 18))

    def _load_initial_state(self):
        ui = self.presenter.get_default_ui_state()
        export_value = {"full": "Pantalla", "tiktok": "TikTok", "both": "Ambos"}[ui["export_mode"]]
        self.export_mode_var.set(export_value)
        self.mode_selector.set(export_value)
        migrated_zoom = UI_DEFAULT_ZOOM if 17 <= ui["zoom"] <= 18 else ui["zoom"]
        self.zoom_spin.set(migrated_zoom)
        self.smooth_slider.set(ui["suavidad"])
        self.fps_spin.set(ui["fps"])
        if HAS_AUDIO and ui["audio"]:
            self.audio_checkbox.select()
        else:
            self.audio_checkbox.deselect()
        self.audio_source_var.set({"system": "Escritorio", "both": "Ambos"}.get(ui.get("audio_mode"), "Microfono"))
        self.preview_enabled_var.set(ui.get("preview_enabled", True))
        self.pause_hotkey_var.set(str(ui.get("pause_hotkey", "f7")).upper())
        self.stop_hotkey_var.set(str(ui.get("stop_hotkey", "f10")).upper())
        self.quality_var.set({
            "low": "Baja",
            "medium": "Media",
            "high": "Alta",
            "very_high": "Muy alta",
        }.get(ui.get("quality", "high"), "Alta"))
        if not HAS_AUDIO:
            self.audio_checkbox.configure(text="Capturar micrófono (instala sounddevice)", state="disabled")
        self.dir_label.configure(text=self._get_video_directory_display())
        self._load_audio_devices()
        self._handle_audio_toggle()
        self._handle_preview_toggle()
        self._refresh_hotkey_labels()
        self.open_last_btn.configure(command=self._reveal_last_export)
        self._update_mode_summary()
        self._update_disk_info()
        self._update_status_text("Listo para grabar", self._success_status_style())
        has_output = bool(self.presenter.get_last_export_path())
        self.open_last_btn.configure(state="normal" if has_output else "disabled")
        self.play_last_btn.configure(state="normal" if has_output else "disabled")

    def _load_audio_devices(self):
        if not HAS_AUDIO:
            self.audio_device_combo.configure(values=["No disponible"], state="disabled")
            return
        audio_mode = self._current_audio_mode()
        if audio_mode in ("system", "both"):
            devices = list_system_audio_devices()
            self.audio_devices["system"] = {name: index for name, index in devices}
            names = [name for name, _index in devices] or ["No disponible"]
        else:
            devices = list_microphone_devices()
            self.audio_devices["mic"] = {name: index for name, index in devices}
            names = [name for name, _index in devices]
        self.audio_device_combo.configure(values=names)
        self.audio_device_combo.set(names[0])
        self._handle_audio_toggle()

    def _get_video_directory_display(self):
        return self.presenter.get_output_dir_display()

    def _get_export_mode(self):
        return {"Pantalla": "full", "TikTok": "tiktok", "Ambos": "both"}[self.export_mode_var.get()]

    def _current_audio_device(self):
        mode = self._current_audio_mode()
        if mode == "both":
            return self.audio_devices.get("system", {}).get(self.audio_device_combo.get())
        return self.audio_devices.get(mode, {}).get(self.audio_device_combo.get())

    def _current_audio_mode(self):
        return {
            "Escritorio": "system",
            "Ambos": "both",
        }.get(self.audio_source_var.get(), "mic")

    def _set_controls_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for widget in (self.mode_selector, self.zoom_spin, self.smooth_slider, self.fps_spin, self.quality_selector, self.change_dir_btn, self.name_input, self.audio_checkbox, self.audio_source_selector, self.audio_device_combo, self.pause_hotkey_button, self.stop_hotkey_button):
            widget.configure(state=state)
        if enabled:
            self._handle_audio_toggle()

    def _update_status_text(self, text, style):
        self.status.configure(text=text, **style)

    def _refresh_hotkey_labels(self):
        pause_label = self._normalize_hotkey_value(self.pause_hotkey_var.get(), "F7")
        stop_label = self._normalize_hotkey_value(self.stop_hotkey_var.get(), "F10")
        self.pause_hotkey_var.set(pause_label)
        self.stop_hotkey_var.set(stop_label)
        self.hotkeys_label.configure(text=f"{pause_label} pausa / reanuda\n{stop_label} termina y renderiza\nLa ventana se minimiza al grabar")

    def _start_hotkey_capture(self, target: str):
        if self.presenter.has_active_recording():
            return
        self._hotkey_capture_target = target
        if target == "pause":
            self.pause_hotkey_var.set("Presiona...")
        else:
            self.stop_hotkey_var.set("Presiona...")
        self.hotkey_capture_hint.configure(text="Presiona una tecla F2-F12. Esc cancela.")
        self.bind("<KeyPress>", self._handle_hotkey_capture, add="+")
        self.focus_force()

    def _finish_hotkey_capture(self):
        self.unbind("<KeyPress>")
        self._hotkey_capture_target = None
        self.hotkey_capture_hint.configure(text="Haz click y presiona una tecla F para asignarla.")
        self._refresh_hotkey_labels()
        self._persist_current_preferences()

    def _handle_hotkey_capture(self, event):
        if self._hotkey_capture_target is None:
            return
        keysym = str(event.keysym or "").upper()
        if keysym == "ESCAPE":
            self._finish_hotkey_capture()
            return
        normalized = self._normalize_hotkey_value(keysym, "")
        if not normalized:
            return
        if self._hotkey_capture_target == "pause":
            self.pause_hotkey_var.set(normalized)
            if self.stop_hotkey_var.get() == normalized:
                self.stop_hotkey_var.set("F10")
        else:
            self.stop_hotkey_var.set(normalized)
            if self.pause_hotkey_var.get() == normalized:
                self.pause_hotkey_var.set("F7")
        self._finish_hotkey_capture()

    @staticmethod
    def _normalize_hotkey_value(value: str, fallback: str) -> str:
        cleaned = (value or "").strip().upper()
        if not cleaned:
            return fallback
        if not cleaned.startswith("F"):
            cleaned = f"F{cleaned}"
        if cleaned[1:].isdigit() and 2 <= int(cleaned[1:]) <= 12:
            return cleaned
        return fallback

    def _update_mode_summary(self):
        mode = self._get_export_mode()
        label = {"full": "16:9 Full HD", "tiktok": "9:16 Vertical", "both": "Dual Export"}[mode]
        quality = self.quality_var.get()
        zoom_value = int(round(self.zoom_spin.get()))
        smooth_value = int(round(self.smooth_slider.get()))
        fps_value = int(round(self.fps_spin.get()))
        self.zoom_value_label.configure(text=f"x {zoom_value / 10:.1f}")
        self.smooth_value_label.configure(text=f"{smooth_value} / {UI_MAX_SUAVIDAD}")
        self.fps_value_label.configure(text=f"{fps_value} FPS")
        self.metric_mode.value_label.configure(text=label)
        self.metric_quality.value_label.configure(text=f"{quality}  |  x {zoom_value / 10:.1f}  |  {fps_value} FPS")
        self.preview_mode_label.configure(text=label)
        self.preview_quality_label.configure(text=f"Seguimiento suave {smooth_value}/{UI_MAX_SUAVIDAD}. Calidad {quality.lower()}. Para salida mas nitida usa zoom x1.0 o x1.1.")

    def _update_recording_time(self):
        recorder = self.presenter.recorder
        if recorder is not None and recorder.is_recording:
            elapsed = recorder.get_elapsed_time()
            self.time_counter.configure(text=f"{int(elapsed // 3600):02d}:{int((elapsed % 3600) // 60):02d}:{int(elapsed % 60):02d}")
        self.clock_job = self.after(100, self._update_recording_time)

    def _schedule_clock(self):
        if self.clock_job is None:
            self._update_recording_time()

    def _cancel_clock(self):
        if self.clock_job is not None:
            self.after_cancel(self.clock_job)
            self.clock_job = None

    def _change_output_directory(self):
        new_dir = filedialog.askdirectory(title="Seleccionar carpeta de destino para videos", initialdir=self.presenter.get_output_dir_display(), mustexist=False)
        if new_dir:
            self.presenter.update_output_directory(Path(new_dir))
            self.dir_label.configure(text=self.presenter.get_output_dir_display())
            self._update_status_text(f"Carpeta actualizada\n{Path(new_dir).name}", self._success_status_style())
            self._update_disk_info()

    def _handle_audio_toggle(self):
        enabled = HAS_AUDIO and bool(self.audio_checkbox.get()) and self.audio_checkbox.cget("state") != "disabled"
        self.audio_source_selector.configure(state="normal" if HAS_AUDIO and self.audio_checkbox.cget("state") != "disabled" else "disabled")
        options = self.audio_device_combo.cget("values")
        has_real_device = bool(options) and options[0] != "No disponible"
        self.audio_device_combo.configure(state="readonly" if enabled and has_real_device else "disabled")
        mode = self._current_audio_mode()
        if mode == "both":
            self.preview_hint_label.configure(text="Audio mixto: microfono por defecto + audio del escritorio seleccionado.")
        elif mode == "system":
            self.preview_hint_label.configure(text="Audio del escritorio desde un dispositivo de captura del sistema.")
        else:
            self.preview_hint_label.configure(text="Preview activo. Puedes apagarlo para ahorrar recursos." if self.preview_enabled_var.get() else "Preview desactivado para reducir consumo dentro de la ventana.")
        if enabled and self.presenter.has_active_recording():
            self.vu_meter.grid()
        else:
            self.vu_meter.grid_remove()

    def _handle_preview_toggle(self):
        enabled = bool(self.preview_enabled_var.get())
        if enabled:
            self.preview_hint_label.configure(text="Preview activo. Puedes apagarlo para ahorrar recursos.")
            if self.presenter.has_active_recording():
                self._schedule_preview()
        else:
            self.preview_hint_label.configure(text="Preview desactivado para reducir consumo dentro de la ventana.")
            self._cancel_preview()
            self.preview_image = None
            self.preview_canvas.configure(image="", text="Preview desactivado", bg="#050b16")

    def toggle(self):
        if not self.presenter.has_active_recording():
            self._start_recording()
            return
        self._stop_recording()

    def _start_recording(self):
        self._set_controls_enabled(False)
        try:
            view_model = self.presenter.start_recording(
                zoom=int(round(self.zoom_spin.get())),
                suavidad=int(round(self.smooth_slider.get())),
                fps=int(round(self.fps_spin.get())),
                custom_name=self.name_input.get().strip(),
                audio=bool(self.audio_checkbox.get()),
                audio_mode=self._current_audio_mode(),
                audio_device=self._current_audio_device() if self.audio_checkbox.get() else None,
                pause_hotkey=self.pause_hotkey_var.get().lower(),
                stop_hotkey=self.stop_hotkey_var.get().lower(),
                quality={
                    "Baja": "low",
                    "Media": "medium",
                    "Alta": "high",
                    "Muy alta": "very_high",
                }.get(self.quality_var.get(), "high"),
            )
        except RecordingEnvironmentError as exc:
            self._set_controls_enabled(True)
            self._update_status_text(f"Error al iniciar\n{exc}", self._error_status_style())
            return
        except Exception as exc:
            self._set_controls_enabled(True)
            self._update_status_text(f"Error inesperado\n{exc}", self._error_status_style())
            return

        recorder = self.presenter.recorder
        recorder.on_pause_toggled = lambda paused: self.after(0, lambda: self._handle_hotkey_pause_changed(paused))
        recorder.on_stop_requested = lambda: self.after(0, self._handle_hotkey_stop)
        self.btn.configure(text=STOP_TEXT, fg_color="#c93b1f", hover_color="#b53118")
        self.header_badge.configure(text="REC")
        self._update_status_text(f"Grabando...\n{Path(recorder.filename).name}\n{self.pause_hotkey_var.get().upper()} pausa o reanuda\n{self.stop_hotkey_var.get().upper()} termina y renderiza", self._recording_status_style())
        if self.preview_enabled_var.get():
            self._schedule_preview()
        self._schedule_clock()
        if self.audio_checkbox.get():
            self.vu_meter.grid()
        self.iconify()

    def _stop_recording(self):
        self._cancel_preview()
        self._cancel_clock()
        self.vu_meter.grid_remove()
        self.preview_canvas.configure(text="Procesando video...", image="", bg="#050b16")
        self.btn.configure(state="disabled")
        mode = self._get_export_mode()
        self.presenter.save_current_preferences(
            zoom=int(round(self.zoom_spin.get())),
            suavidad=int(round(self.smooth_slider.get())),
            fps=int(round(self.fps_spin.get())),
            export_mode=mode,
            preview_enabled=bool(self.preview_enabled_var.get()),
            pause_hotkey=self.pause_hotkey_var.get().lower(),
            stop_hotkey=self.stop_hotkey_var.get().lower(),
            quality={
                "Baja": "low",
                "Media": "medium",
                "Alta": "high",
                "Muy alta": "very_high",
            }.get(self.quality_var.get(), "high"),
        )
        self.header_badge.configure(text="RENDER")
        render_label = {"full": "pantalla completa", "tiktok": "TikTok 9:16", "both": "ambos formatos"}[mode]
        self._update_status_text(f"Renderizando {render_label}...", self._rendering_status_style())
        self.progress_bar.set(0)
        self.render_thread = threading.Thread(target=self._render_worker, args=(mode,), daemon=True)
        self.render_thread.start()

    def _render_worker(self, mode):
        try:
            result = self.presenter.stop_recording(
                mode,
                callback_progress=lambda value: self.after(0, lambda v=value: self.progress_bar.set(v / 100)),
            )
            self.after(0, lambda: self.on_finished(result))
        except Exception as exc:
            self.after(0, lambda e=exc: self._handle_render_error(e))

    def on_finished(self, result):
        self.deiconify()
        self.lift()
        self.focus_force()
        view_model = self.presenter.build_finished_view_model(result)
        self.btn.configure(state="normal", text=START_TEXT, fg_color="#ff6b2c", hover_color="#ff5a14")
        self.header_badge.configure(text="LISTO")
        lines = ["Guardado:"]
        if view_model.full_path:
            lines.append(f"Full: {Path(view_model.full_path).name}")
        if view_model.tiktok_path:
            lines.append(f"TikTok: {Path(view_model.tiktok_path).name}")
        self._update_status_text("\n".join(lines), self._success_status_style())
        self.progress_bar.set(0)
        self.preview_canvas.configure(text="Sin señal", image="", bg="#050b16")
        self.preview_image = None
        self._handle_preview_toggle()
        self._set_controls_enabled(True)
        self._update_disk_info()
        has_output = bool(view_model.primary_path)
        self.open_last_btn.configure(state="normal" if has_output else "disabled")
        self.play_last_btn.configure(state="normal" if has_output else "disabled")

    def _handle_render_error(self, exc):
        self.deiconify()
        self.btn.configure(state="normal", text=START_TEXT, fg_color="#ff6b2c", hover_color="#ff5a14")
        self.header_badge.configure(text="ERROR")
        self._update_status_text(f"Error al renderizar\n{exc}", self._error_status_style())
        self._set_controls_enabled(True)

    def _handle_hotkey_stop(self):
        if self.presenter.has_active_recording() and self.btn.cget("state") != "disabled":
            self.deiconify()
            self.lift()
            self.focus_force()
            self.toggle()

    def _handle_hotkey_pause_changed(self, paused):
        pause_label = self.pause_hotkey_var.get().upper()
        stop_label = self.stop_hotkey_var.get().upper()
        if paused:
            self.header_badge.configure(text="PAUSA")
            self.preview_hint_label.configure(text="Captura pausada. El último frame queda visible.")
            self._update_status_text(
                f"Grabación en pausa\n{pause_label} reanuda\n{stop_label} termina",
                self._rendering_status_style(),
            )
            return
        self.header_badge.configure(text="REC")
        self._handle_preview_toggle()
        self._update_status_text(
            f"Grabando ahora\n{pause_label} pausa o reanuda\n{stop_label} termina",
            self._recording_status_style(),
        )

    def _schedule_preview(self):
        if self.preview_job is None and self.preview_enabled_var.get():
            self._update_preview()

    def _cancel_preview(self):
        if self.preview_job is not None:
            self.after_cancel(self.preview_job)
            self.preview_job = None

    def _update_preview(self):
        if not self.preview_enabled_var.get():
            self.preview_job = None
            return
        recorder = self.presenter.recorder
        if recorder is not None:
            mode = self._get_export_mode()
            frame = recorder.preview_frame_tiktok if mode == "tiktok" else recorder.preview_frame
            if frame is not None:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(rgb)
                width = max(self.preview_canvas.winfo_width(), 520)
                height = max(self.preview_canvas.winfo_height(), 220)
                image.thumbnail((width, height), Image.Resampling.LANCZOS)
                self.preview_image = ImageTk.PhotoImage(image=image)
                self.preview_canvas.configure(image=self.preview_image, text="")
            if self.audio_checkbox.get():
                self.vu_meter.set(max(0, min(recorder.audio_level / 100, 1)))
            self._disk_tick = (self._disk_tick + 1) % 15
            if self._disk_tick == 0:
                self._update_disk_info()
        self.preview_job = self.after(33, self._update_preview)

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
        text = f"{free_gb:.1f} GB libres"
        if temp_mb > 0:
            text += f"  |  Temp {temp_mb:.0f} MB"
        self.metric_disk.value_label.configure(text=text)

    def _open_output_folder(self):
        if not self.presenter.reveal_output_directory():
            self._update_status_text("No se pudo abrir la carpeta de salida.", self._error_status_style())

    def _reveal_last_export(self):
        if not self.presenter.reveal_last_export():
            self._update_status_text("No se encontro un video reciente para mostrar.", self._error_status_style())

    def _play_last_export(self):
        target = self.presenter.get_last_export_path()
        if not target:
            return
        target_path = str(Path(target).resolve())
        try:
            if os.name == "nt":
                os.startfile(target_path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", target_path])
            else:
                subprocess.Popen(["xdg-open", target_path])
        except Exception as exc:
            self._update_status_text(f"No se pudo reproducir\n{exc}", self._error_status_style())

    def _on_close(self):
        if self.presenter.has_active_recording():
            self.iconify()
            return
        self._persist_current_preferences()
        self._cancel_preview()
        self._cancel_clock()
        self.destroy()

    def _persist_current_preferences(self):
        self.presenter.save_current_preferences(
            zoom=int(round(self.zoom_spin.get())),
            suavidad=int(round(self.smooth_slider.get())),
            fps=int(round(self.fps_spin.get())),
            export_mode=self._get_export_mode(),
            audio=bool(self.audio_checkbox.get()),
            audio_mode=self._current_audio_mode(),
            preview_enabled=bool(self.preview_enabled_var.get()),
            pause_hotkey=self.pause_hotkey_var.get().lower(),
            stop_hotkey=self.stop_hotkey_var.get().lower(),
            quality={
                "Baja": "low",
                "Media": "medium",
                "Alta": "high",
                "Muy alta": "very_high",
            }.get(self.quality_var.get(), "high"),
        )

    @staticmethod
    def _success_status_style():
        return {"fg_color": "#d9fbe6", "text_color": "#14532d"}

    @staticmethod
    def _recording_status_style():
        return {"fg_color": "#ffe8dd", "text_color": "#9a3412"}

    @staticmethod
    def _rendering_status_style():
        return {"fg_color": "#dbeafe", "text_color": "#1d4ed8"}

    @staticmethod
    def _error_status_style():
        return {"fg_color": "#fee2e2", "text_color": "#991b1b"}
