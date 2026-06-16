import os
import subprocess
import glob
from app.core.settings_service import get_setting, is_ffmpeg_available
import app.core.log_service as log_service

def compile_video(image_pattern, output_path, fps=24, fps_base=1):
    """
    Compiles an image sequence into an MP4 video using FFmpeg.
    image_pattern: path pattern like "C:\\renders\\Cam_A\\####.png" (Blender style)
                   or "C:\\renders\\Cam_A\\%04d.png" (FFmpeg style)
    """
    ffmpeg_bin = get_setting("ffmpeg_path", "ffmpeg")
    
    if not is_ffmpeg_available(ffmpeg_bin):
        log_service.warning("FFmpeg no está disponible. Saltando compilación de video.")
        return False, "FFmpeg no está instalado o no se encontró en la ruta configurada."
    
    # Resolve Blender style '####' to FFmpeg style '%04d'
    # Blender output often has '####' in the pattern
    ffmpeg_input = image_pattern.replace("####", "%04d")
    
    # Calculate framerate ratio
    framerate_str = f"{fps}/{fps_base}" if fps_base and fps_base != 1 else str(fps)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    cmd = [
        ffmpeg_bin,
        "-y",               # Overwrite output files without asking
        "-framerate", framerate_str,
        "-i", ffmpeg_input,
        "-c:v", "libx264",  # H.264 video codec
        "-pix_fmt", "yuv420p", # Standard pixel format for maximum compatibility
        output_path
    ]
    
    log_service.info(f"Compilando video con FFmpeg: {' '.join(cmd)}")
    
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
            startupinfo=startupinfo
        )
        
        if result.returncode != 0:
            log_service.error(f"Fallo al compilar video con FFmpeg (Código {result.returncode}). Stderr:\n{result.stderr}")
            return False, f"FFmpeg falló (Código {result.returncode})"
            
        log_service.info(f"Video compilado con éxito: {output_path}")
        return True, ""
    except Exception as e:
        log_service.error(f"Excepción al ejecutar FFmpeg: {e}")
        return False, str(e)

def generate_thumbnail(image_path, output_path, width=320):
    """
    Generates a downscaled JPEG thumbnail from an image using FFmpeg.
    This runs instantly and does not require PIL/Pillow.
    """
    ffmpeg_bin = get_setting("ffmpeg_path", "ffmpeg")
    
    if not is_ffmpeg_available(ffmpeg_bin):
        return False
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", image_path,
        "-vf", f"scale={width}:-1", # scale width, auto-calculate height keeping aspect ratio
        "-q:v", "5",                 # JPEG quality (1-31, lower is better, 5 is good quality/size balance)
        output_path
    ]
    
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo
        )
        if result.returncode == 0 and os.path.exists(output_path):
            return True
        return False
    except Exception as e:
        log_service.error(f"Excepción al generar miniatura con FFmpeg: {e}")
        return False
