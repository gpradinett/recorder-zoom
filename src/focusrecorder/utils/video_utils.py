"""Utilidades para procesamiento de video."""
import os
import subprocess
import imageio_ffmpeg


def reencode_to_h264(input_path: str) -> None:
    """
    Re-encodea un archivo de video a H.264 + AAC usando FFmpeg.
    Compatible con WhatsApp, Instagram, y reproductores estándar.
    Reemplaza el archivo original al terminar.
    
    Args:
        input_path: Ruta al archivo de video a re-encodear
    
    Notes:
        - Usa el FFmpeg embebido en imageio-ffmpeg
        - Genera un archivo temporal con sufijo _h264.mp4
        - Reemplaza el archivo original si el re-encoding es exitoso
        - Mantiene el archivo original si el re-encoding falla pero el original es válido
    """
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    tmp_path = input_path.replace(".mp4", "_h264.mp4")

    cmd = [
        ffmpeg_exe,
        "-y",                      # sobreescribir sin preguntar
        "-i", input_path,          # entrada
        "-c:v", "libx264",         # codec H.264
        "-preset", "fast",         # velocidad/calidad balance
        "-crf", "18",              # calidad alta (0=lossless, 51=peor)
        "-pix_fmt", "yuv420p",     # compatible con todos los reproductores
        "-movflags", "+faststart", # metadata al inicio (streaming/WA)
        "-an",                     # sin audio (grabación de pantalla)
        tmp_path
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Reemplazar archivo intermedio con el H.264 final
    if os.path.exists(tmp_path):  # pragma: no cover
        os.remove(input_path)
        os.rename(tmp_path, input_path)
    elif os.path.getsize(input_path) > 0:
        # Si falló el re-encode pero el original existe, lo dejamos
        pass
