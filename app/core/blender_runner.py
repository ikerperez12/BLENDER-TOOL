import os
import subprocess
import re
import psutil
from PySide6.QtCore import QObject, Signal
import app.core.log_service as log_service
from app.core.settings_service import get_setting, get_base_dir

def safe_filename(name):
    if not name:
        return "unknown"
    # Replace invalid chars: \ / : * ? " < > |
    import re
    return re.sub(r'[\s\\/:*?"<>|]', '_', name)

class BlenderRunner(QObject):
    # Signals for UI communication
    log_received = Signal(str)
    progress_changed = Signal(int)
    status_message = Signal(str)
    finished = Signal(int, str)  # return_code, error_summary

    def __init__(self, project_code, job_id, camera_name, job_type=None, log_path=None):
        super().__init__()
        self.project_code = project_code
        self.job_id = job_id
        self.camera_name = camera_name
        self.job_type = job_type
        
        # Sanitise camera_name for log path
        safe_cam = safe_filename(camera_name)
        
        if log_path:
            self.log_path = log_path
        else:
            log_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "IP Blender Tool", "logs")
            self.log_path = os.path.join(log_dir, f"job_{job_id}_{safe_cam}.log")
            
        self.process = None
        self.is_cancelled = False

    def kill_process_tree(self):
        """Kills the blender process and all its children recursively."""
        if not self.process:
            return
            
        pid = self.process.pid
        log_service.info(f"Cancelando proceso y matando árbol de procesos de PID {pid}...", self.project_code)
        
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # Terminate children first
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            
            # Terminate parent
            try:
                parent.terminate()
            except psutil.NoSuchProcess:
                pass
                
            # Wait for them to exit
            gone, alive = psutil.wait_procs(children + [parent], timeout=3)
            
            # Force kill any survivors
            for proc in alive:
                try:
                    proc.kill()
                except psutil.NoSuchProcess:
                    pass
                    
            log_service.info("Árbol de procesos terminado con éxito.", self.project_code)
        except Exception as e:
            log_service.error(f"Error al matar el árbol de procesos: {e}", self.project_code)
            # Windows fallback
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception:
                pass

    def cancel(self):
        """Triggers process cancellation."""
        self.is_cancelled = True
        if self.process:
            self.kill_process_tree()

    def run_still_render(self, blend_path, camera_name, output_path, profile="Client", res_pct=100, engine="", device="GPU", frame=1):
        """Runs a still image render for a single camera."""
        blender_bin = get_setting("blender_path")
        if not blender_bin:
            self.finished.emit(-1, "Ruta de Blender no configurada.")
            return

        script_path = os.path.join(
            get_base_dir(),
            "blender_scripts",
            "render_camera.py"
        )

        args = [
            blender_bin,
            "-b", blend_path,
            "--python-exit-code", "1",
            "--python", script_path,
            "--",
            "--camera", camera_name,
            "--output", output_path,
            "--profile", profile,
            "--res-pct", str(res_pct),
            "--device", device,
            "--frame-start", str(frame),
            "--frame-end", str(frame)
        ]

        if engine:
            args.extend(["--engine", engine])

        self._execute_blender(args, frame_mode=False)

    def run_animation_render(self, blend_path, camera_name, output_path, frame_start, frame_end, profile="Client", res_pct=100, engine="", device="GPU"):
        """Runs an animation render sequence for a camera."""
        blender_bin = get_setting("blender_path")
        if not blender_bin:
            self.finished.emit(-1, "Ruta de Blender no configurada.")
            return

        script_path = os.path.join(
            get_base_dir(),
            "blender_scripts",
            "render_camera.py"
        )

        args = [
            blender_bin,
            "-b", blend_path,
            "--python-exit-code", "1",
            "--python", script_path,
            "--",
            "--camera", camera_name,
            "--output", output_path,
            "--profile", profile,
            "--res-pct", str(res_pct),
            "--device", device,
            "--frame-start", str(frame_start),
            "--frame-end", str(frame_end),
            "--is-animation"
        ]

        if engine:
            args.extend(["--engine", engine])

        self._execute_blender(args, frame_mode=True, frame_start=frame_start, frame_end=frame_end)

    def run_montage_render(self, montage_blend_path, img_path, output_path):
        """Runs a montage composition render."""
        blender_bin = get_setting("blender_path")
        if not blender_bin:
            self.finished.emit(-1, "Ruta de Blender no configurada.")
            return

        script_path = os.path.join(
            get_base_dir(),
            "blender_scripts",
            "update_compositor.py"
        )

        args = [
            blender_bin,
            "-b", montage_blend_path,
            "--python-exit-code", "1",
            "--python", script_path,
            "--",
            "--img-path", img_path,
            "--output", output_path
        ]

        self._execute_blender(args, frame_mode=False, is_montage=True)

    def _execute_blender(self, args, frame_mode=False, frame_start=1, frame_end=1, is_montage=False):
        import json
        self.is_cancelled = False
        
        # Check if we should run in Mock Mode (for demo project "0000" if Blender is not configured/found)
        is_demo = any("0000" in str(arg) for arg in args)
        blender_bin = get_setting("blender_path")
        blender_exists = blender_bin and os.path.exists(blender_bin)
        
        if is_demo and not blender_exists:
            self._execute_mock_render(args, frame_mode, frame_start, frame_end, is_montage)
            return
            
        log_service.info(f"Ejecutando comando: {' '.join(args)}", self.project_code)
        
        # Ensure log directory exists
        log_file_path = self.log_path
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            self.process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Redirect stderr to stdout so we read both
                text=True,
                encoding="utf-8",
                errors="ignore",
                startupinfo=startupinfo
            )
            
            error_lines = []
            
            # Open the raw log file in write mode
            with open(log_file_path, "w", encoding="utf-8", errors="ignore") as log_file:
                while True:
                    line = self.process.stdout.readline()
                    if not line:
                        break
                    
                    # Write to raw log file synchronously
                    log_file.write(line)
                    log_file.flush()
                    
                    line_str = line.strip()
                    if not line_str:
                        continue
                    
                    # Log service backup
                    log_service.info(line_str, self.project_code)
                    
                    # Check if line is an IPBT_EVENT
                    if line_str.startswith("IPBT_EVENT "):
                        try:
                            event_data = json.loads(line_str[11:])
                            ev_type = event_data.get("type")
                            phase = event_data.get("phase")
                            ev_msg = event_data.get("message")
                            
                            # Emit message to UI if present
                            if ev_msg:
                                self.status_message.emit(ev_msg)
                                
                            # Segregate logs based on severity / type
                            if ev_type == "error":
                                err_msg = f"[ERROR] {event_data.get('code', 'RENDER_ERROR')}: {ev_msg}"
                                self.log_received.emit(err_msg)
                                error_lines.append(err_msg)
                            elif ev_type == "warning":
                                self.log_received.emit(f"[ADVERTENCIA] {ev_msg}")
                            elif ev_type in ["job_started", "blend_loaded", "scene_prepared", "render_started", "render_saved", "compositor_started", "compositor_image_replaced", "compositor_saved", "job_completed"]:
                                if ev_msg:
                                    self.log_received.emit(f"[INFO] {ev_msg}")
                            
                            # Calculate real progress percentages based on events
                            if frame_mode:  # ANIMATION: base on completed physical frames
                                if ev_type == "frame_done":
                                    completed = event_data.get("frame", 0)
                                    total = event_data.get("total_frames", 1)
                                    if total > 0:
                                        pct = int(100.0 * completed / total)
                                        pct = max(0, min(100, pct))
                                        self.progress_changed.emit(pct)
                                elif ev_type == "job_started":
                                    self.progress_changed.emit(0)
                            else:  # STILL RENDER or MONTAGE
                                if phase == "launch":
                                    self.progress_changed.emit(0)
                                elif phase == "load":
                                    self.progress_changed.emit(5)
                                elif phase == "prepare":
                                    self.progress_changed.emit(10)
                                elif phase == "render":
                                    if ev_type == "progress_update":
                                        # Cycles samples update
                                        curr = event_data.get("current", 0)
                                        total = event_data.get("total", 0)
                                        if total > 0:
                                            pct = int(10.0 + 85.0 * curr / total)
                                            pct = max(10, min(95, pct))
                                            self.progress_changed.emit(pct)
                                    elif ev_type in ["render_started", "frame_started"]:
                                        # Set to indeterminate state (-1) if we just started render
                                        # It will stay indeterminate unless Cycles progress_update starts coming
                                        self.progress_changed.emit(-1)
                                elif phase == "save":
                                    self.progress_changed.emit(95)
                                elif phase == "complete" or ev_type == "job_completed":
                                    self.progress_changed.emit(100)
                                    
                        except Exception as parse_err:
                            log_service.error(f"Error parsing IPBT_EVENT: {parse_err}", self.project_code)
                    else:
                        # Non-event line: show only warnings and errors in UI console
                        upper_line = line_str.upper()
                        # Capture potential critical system errors
                        if any(err in upper_line for err in ["OUT OF MEMORY", "CUDA ERROR", "OPTIX ERROR", "MISSING TEXTURES", "PERMISSION DENIED"]):
                            error_lines.append(line_str)
                            self.log_received.emit(line_str)
                        else:
                            # Filter standard output to only display warnings, errors, or exceptions
                            is_important = any(kw in upper_line for kw in ["ERROR", "WARNING", "EXCEPTION", "FAIL", "FATAL"])
                            # Make sure we don't spam sample or frame logs
                            is_spam = any(kw in upper_line for kw in ["SAMPLE", "RENDERING", "FRA:"])
                            if is_important and not is_spam:
                                self.log_received.emit(line_str)
                                
            self.process.wait()
            return_code = self.process.returncode
            
            if self.is_cancelled:
                self.finished.emit(-2, "Operación cancelada por el usuario.")
            elif return_code != 0:
                summary = "Error en el renderizado de Blender."
                if error_lines:
                    summary = " | ".join(error_lines[:2])
                self.finished.emit(return_code, summary)
            else:
                self.progress_changed.emit(100)
                self.finished.emit(0, "")
                
        except Exception as e:
            log_service.error(f"Excepción al ejecutar Blender: {e}", self.project_code)
            self.finished.emit(-1, str(e))
        finally:
            self.process = None

    def _execute_mock_render(self, args, frame_mode=False, frame_start=1, frame_end=1, is_montage=False):
        """Simulates rendering progress and writes a mock PNG/JPG output file."""
        import time
        self.log_received.emit("=== MODO SIMULADO / DEMO ACTIVO ===")
        log_service.warning("Iniciando renderizado mock para el Proyecto Demo (Blender no configurado).", self.project_code)
        
        # Locate the --output argument to write a mock image
        output_path = None
        for i, arg in enumerate(args):
            if arg == "--output" and i + 1 < len(args):
                output_path = args[i + 1]
                break
                
        steps = 10
        for step in range(steps + 1):
            if self.is_cancelled:
                self.log_received.emit("❌ Renderizado simulado cancelado por el usuario.")
                self.finished.emit(-2, "Operación cancelada por el usuario.")
                return
                
            pct = int(100.0 * step / steps)
            self.progress_changed.emit(pct)
            if is_montage:
                self.log_received.emit(f"Montaje simulado en progreso... {pct}%")
            else:
                self.log_received.emit(f"Procesando muestras de cámara (simulado)... {pct}%")
            time.sleep(0.2)
            
        if output_path:
            try:
                # 1. Save in the main target output path so database/post-verification checks succeed
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "wb") as f:
                    # 1x1 transparent PNG bytes for dummy file
                    f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82')
                self.log_received.emit(f"✅ Archivo renderizado simulado guardado en: {output_path}")
                
                # 2. Also save in a separate demo subfolder to avoid mixing with real outputs (as user requested)
                demo_out_dir = os.path.join(os.path.dirname(output_path), "demo_renders")
                os.makedirs(demo_out_dir, exist_ok=True)
                demo_file_path = os.path.join(demo_out_dir, os.path.basename(output_path))
                with open(demo_file_path, "wb") as f:
                    f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82')
                self.log_received.emit(f"✅ Copia demo guardada en carpeta aislada: {demo_file_path}")
            except Exception as e:
                self.log_received.emit(f"⚠️ No se pudo guardar el archivo simulado: {e}")
                
        self.progress_changed.emit(100)
        self.finished.emit(0, "")
