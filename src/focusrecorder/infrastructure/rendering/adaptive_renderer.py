import cv2
import numpy as np

from ..encoding.h264_encoder import reencode_to_h264


class AdaptiveVideoRenderer:
    def render(
        self,
        *,
        raw_data,
        settings,
        screen_size,
        output_filename,
        callback_progress=None,
        export_mode="full",
    ):
        if not raw_data:
            return

        sw, sh = screen_size
        total_duration = raw_data[-1][4]
        target_fps = int(settings.fps)
        total_frames = max(int(total_duration * target_fps), 1)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore[attr-defined]

        do_full = export_mode in ("full", "both")
        do_tiktok = export_mode in ("tiktok", "both")

        out_full = None
        if do_full:
            out_full = cv2.VideoWriter(output_filename, fourcc, target_fps, (sw, sh))

        out_tiktok = None
        tiktok_w = tiktok_h = 0
        tiktok_path = ""
        if do_tiktok:
            tiktok_h = sh
            tiktok_w = int(sh * 9 / 16)
            if tiktok_w % 2 != 0:  # pragma: no cover
                tiktok_w += 1
            tiktok_path = output_filename.replace(".mp4", "_tiktok.mp4")
            out_tiktok = cv2.VideoWriter(tiktok_path, fourcc, target_fps, (tiktok_w, tiktok_h))

        cam_x = float(sw // 2)
        cam_y = float(sh // 2)
        tiktok_cam_x = float(sw // 2)
        tiktok_cam_y = float(sh // 2)
        tiktok_smooth = min(settings.suavidad * 1.5, 1.0)
        data_ptr = 0
        render_weight = 0.8

        for f_idx in range(total_frames):
            current_time = f_idx / target_fps

            while data_ptr < len(raw_data) - 1 and raw_data[data_ptr + 1][4] < current_time:
                data_ptr += 1

            frame, mx, my, clicking, _ = raw_data[data_ptr]
            color = (0, 215, 255) if clicking else (255, 255, 255)
            zn = settings.zoom

            if do_full:
                cam_x += (mx - cam_x) * settings.suavidad
                cam_y += (my - cam_y) * settings.suavidad

                z_w = int(sw / zn)
                z_h = int(sh / zn)
                x1 = int(np.clip(cam_x - z_w // 2, 0, sw - z_w))
                y1 = int(np.clip(cam_y - z_h // 2, 0, sh - z_h))

                cropped = frame[y1:y1 + z_h, x1:x1 + z_w]

                if cropped.size > 0:  # pragma: no cover
                    final = cv2.resize(cropped, (sw, sh), interpolation=cv2.INTER_LANCZOS4)

                    vx = int(np.clip((mx - x1) * (sw / z_w), 0, sw - 1))
                    vy = int(np.clip((my - y1) * (sh / z_h), 0, sh - 1))
                    cv2.circle(final, (vx, vy), 8, color, -1 if clicking else 2, lineType=cv2.LINE_AA)
                    out_full.write(final)  # type: ignore[union-attr]

            if do_tiktok:
                tiktok_cam_x += (mx - tiktok_cam_x) * tiktok_smooth
                tiktok_cam_y += (my - tiktok_cam_y) * tiktok_smooth

                z_h_tt = int(sh / zn)
                z_w_tt = min(int(z_h_tt * 9 / 16), sw)
                z_h_tt = min(z_h_tt, sh)

                x1_tt = int(np.clip(tiktok_cam_x - z_w_tt // 2, 0, sw - z_w_tt))
                y1_tt = int(np.clip(tiktok_cam_y - z_h_tt // 2, 0, sh - z_h_tt))

                cropped_tt = frame[y1_tt:y1_tt + z_h_tt, x1_tt:x1_tt + z_w_tt]

                if cropped_tt.size > 0 and tiktok_w > 0 and tiktok_h > 0:  # pragma: no cover
                    final_tt = cv2.resize(cropped_tt, (tiktok_w, tiktok_h), interpolation=cv2.INTER_LANCZOS4)
                    tx = int(np.clip((mx - x1_tt) * (tiktok_w / z_w_tt), 0, tiktok_w - 1))
                    ty = int(np.clip((my - y1_tt) * (tiktok_h / z_h_tt), 0, tiktok_h - 1))
                    cv2.circle(final_tt, (tx, ty), 8, color, -1 if clicking else 2, lineType=cv2.LINE_AA)
                    out_tiktok.write(final_tt)  # type: ignore[union-attr]

            if callback_progress and f_idx % 10 == 0:
                pct = int((f_idx / total_frames) * 100 * render_weight)
                callback_progress(pct)

        if out_full:
            out_full.release()
        if out_tiktok:
            out_tiktok.release()

        files_to_encode = []
        if do_full:
            files_to_encode.append(output_filename)
        if do_tiktok:
            files_to_encode.append(tiktok_path)

        for i, path in enumerate(files_to_encode):
            reencode_to_h264(path)
            if callback_progress:
                base = int(100 * render_weight)
                pct = base + int((i + 1) / len(files_to_encode) * (100 - base))
                callback_progress(pct)

        if callback_progress:
            callback_progress(100)

    def render_from_file(
        self,
        *,
        temp_path,
        mouse_data,
        settings,
        screen_size,
        output_filename,
        callback_progress=None,
        export_mode="full",
    ):
        cap = cv2.VideoCapture(temp_path)
        total_frames_recorded = len(mouse_data)

        if not cap.isOpened() or total_frames_recorded == 0:
            cap.release()
            return

        total_duration = mouse_data[-1][3]
        target_fps = int(settings.fps)
        total_target_frames = max(int(total_duration * target_fps), 1)

        sw, sh = screen_size
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore[attr-defined]
        render_weight = 0.8

        do_full = export_mode in ("full", "both")
        do_tiktok = export_mode in ("tiktok", "both")

        out_full = None
        if do_full:
            out_full = cv2.VideoWriter(output_filename, fourcc, target_fps, (sw, sh))

        out_tiktok = None
        tiktok_w = tiktok_h = 0
        tiktok_path = ""
        if do_tiktok:
            tiktok_h = sh
            tiktok_w = int(sh * 9 / 16)
            if tiktok_w % 2 != 0:  # pragma: no cover
                tiktok_w += 1
            tiktok_path = output_filename.replace(".mp4", "_tiktok.mp4")
            out_tiktok = cv2.VideoWriter(tiktok_path, fourcc, target_fps, (tiktok_w, tiktok_h))

        cam_x = float(sw // 2)
        cam_y = float(sh // 2)
        tiktok_cam_x = float(sw // 2)
        tiktok_cam_y = float(sh // 2)
        tiktok_smooth = min(settings.suavidad * 1.5, 1.0)
        zn = settings.zoom

        data_ptr = 0
        ret, current_frame = cap.read()
        if not ret:
            cap.release()
            return

        for f_idx in range(total_target_frames):
            current_time = f_idx / target_fps

            while data_ptr < total_frames_recorded - 1 and mouse_data[data_ptr + 1][3] < current_time:
                data_ptr += 1
                ret, next_frame = cap.read()
                if ret:
                    current_frame = next_frame

            mx, my, clicking, _ = mouse_data[data_ptr]
            color = (0, 215, 255) if clicking else (255, 255, 255)
            frame = current_frame

            if do_full and out_full:
                cam_x += (mx - cam_x) * settings.suavidad
                cam_y += (my - cam_y) * settings.suavidad

                z_w = int(sw / zn)
                z_h = int(sh / zn)
                x1 = int(np.clip(cam_x - z_w // 2, 0, sw - z_w))
                y1 = int(np.clip(cam_y - z_h // 2, 0, sh - z_h))

                cropped = frame[y1:y1 + z_h, x1:x1 + z_w]
                if cropped.size > 0:  # pragma: no cover
                    final = cv2.resize(cropped, (sw, sh), interpolation=cv2.INTER_LANCZOS4)
                    vx = int(np.clip((mx - x1) * (sw / z_w), 0, sw - 1))
                    vy = int(np.clip((my - y1) * (sh / z_h), 0, sh - 1))
                    cv2.circle(final, (vx, vy), 8, color, -1 if clicking else 2, lineType=cv2.LINE_AA)
                    out_full.write(final)

            if do_tiktok and out_tiktok:
                tiktok_cam_x += (mx - tiktok_cam_x) * tiktok_smooth
                tiktok_cam_y += (my - tiktok_cam_y) * tiktok_smooth

                z_h_tt = int(sh / zn)
                z_w_tt = min(int(z_h_tt * 9 / 16), sw)
                z_h_tt = min(z_h_tt, sh)

                x1_tt = int(np.clip(tiktok_cam_x - z_w_tt // 2, 0, sw - z_w_tt))
                y1_tt = int(np.clip(tiktok_cam_y - z_h_tt // 2, 0, sh - z_h_tt))

                cropped_tt = frame[y1_tt:y1_tt + z_h_tt, x1_tt:x1_tt + z_w_tt]
                if cropped_tt.size > 0 and tiktok_w > 0 and tiktok_h > 0:  # pragma: no cover
                    final_tt = cv2.resize(cropped_tt, (tiktok_w, tiktok_h), interpolation=cv2.INTER_LANCZOS4)
                    tx = int(np.clip((mx - x1_tt) * (tiktok_w / z_w_tt), 0, tiktok_w - 1))
                    ty = int(np.clip((my - y1_tt) * (tiktok_h / z_h_tt), 0, tiktok_h - 1))
                    cv2.circle(final_tt, (tx, ty), 8, color, -1 if clicking else 2, lineType=cv2.LINE_AA)
                    out_tiktok.write(final_tt)

            if callback_progress and f_idx % 10 == 0:
                callback_progress(int((f_idx / total_target_frames) * 100 * render_weight))

        cap.release()

        files_to_encode = []
        if out_full:
            out_full.release()
            files_to_encode.append(output_filename)
        if out_tiktok:
            out_tiktok.release()
            files_to_encode.append(tiktok_path)

        for i, path in enumerate(files_to_encode):
            reencode_to_h264(path)
            if callback_progress:
                base = int(100 * render_weight)
                callback_progress(base + int((i + 1) / len(files_to_encode) * (100 - base)))

        if callback_progress:
            callback_progress(100)
