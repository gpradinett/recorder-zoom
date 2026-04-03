import cv2
import numpy as np
import dxcam
import pyautogui
import threading
from pynput import mouse
import time

class FocusRecorder:
    _camera_instance = None

    def __init__(self, filename="focus_video.mp4", config=None):
        if FocusRecorder._camera_instance is None:
            FocusRecorder._camera_instance = dxcam.create(output_color="BGR")
        
        self.camera = FocusRecorder._camera_instance
        self.filename = filename
        self.config = config
        self.is_recording = False
        self.sw, self.sh = pyautogui.size()
        self.raw_data = [] 
        self.is_clicking = False

    def _on_click(self, x, y, button, pressed):
        self.is_clicking = pressed

    def start(self):
        self.is_recording = True
        self.raw_data = []
        self.start_time = time.perf_counter()
        self.listener = mouse.Listener(on_click=self._on_click)
        self.listener.start()
        self.thread = threading.Thread(target=self._record_loop)
        self.thread.start()

    def stop(self, callback_progress=None):
        self.is_recording = False
        if hasattr(self, 'listener'): self.listener.stop()
        self.thread.join()
        self._render_adaptive_video(callback_progress)

    def _record_loop(self):
        self.camera.start(target_fps=0) 
        while self.is_recording:
            frame = self.camera.get_latest_frame()
            if frame is None: continue
            mx, my = pyautogui.position()
            ts = time.perf_counter() - self.start_time
            self.raw_data.append((frame.copy(), mx, my, self.is_clicking, ts))
            time.sleep(0.001) 
        self.camera.stop()

    def _render_adaptive_video(self, callback_progress):
            if not self.raw_data: return
            
            total_duration = self.raw_data[-1][4]
            target_fps = int(self.config['fps'])
            total_frames_to_render = int(total_duration * target_fps)
            
            # --- MEJORA DE CODEC Y CALIDAD ---
            # 'avc1' es el estándar H.264, mejor que 'mp4v' para calidad/tamaño
            fourcc = cv2.VideoWriter_fourcc(*'avc1') 
            
            out = cv2.VideoWriter(self.filename, fourcc, target_fps, (self.sw, self.sh))

            cam_x, cam_y = self.sw // 2, self.sh // 2
            data_ptr = 0

            for f_idx in range(total_frames_to_render):
                current_video_time = f_idx / target_fps
                while data_ptr < len(self.raw_data) - 1 and self.raw_data[data_ptr + 1][4] < current_video_time:
                    data_ptr += 1
                
                frame, mx, my, clicking, _ = self.raw_data[data_ptr]
                
                # Suavizado de cámara
                cam_x += (mx - cam_x) * self.config['suavidad']
                cam_y += (my - cam_y) * self.config['suavidad']
                
                zn = self.config['zoom']
                z_w, z_h = int(self.sw / zn), int(self.sh / zn)
                x1 = int(np.clip(cam_x - z_w // 2, 0, self.sw - z_w))
                y1 = int(np.clip(cam_y - z_h // 2, 0, self.sh - z_h))

                # --- CAMBIO CLAVE: REESCALADO DE ALTA FIDELIDAD ---
                cropped = frame[y1:y1+z_h, x1:x1+z_w]
                
                # INTER_LANCZOS4 es el estándar de oro para evitar borrosidad en textos
                final_frame = cv2.resize(cropped, (self.sw, self.sh), interpolation=cv2.INTER_LANCZOS4)

                # Dibujar cursor con antialiasing (line_aa para bordes suaves)
                vx, vy = int((mx - x1) * (self.sw / z_w)), int((my - y1) * (self.sh / z_h))
                color = (0, 215, 255) if clicking else (255, 255, 255)
                cv2.circle(final_frame, (vx, vy), 8, color, -1 if clicking else 2, lineType=cv2.LINE_AA)

                out.write(final_frame)
                
                if callback_progress and f_idx % 10 == 0:
                    percent = int((f_idx / total_frames_to_render) * 100)
                    callback_progress(percent)

            out.release()