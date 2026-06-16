import os
import time
import datetime
import re
from PySide6.QtCore import QThread, Signal
from app.core.db import get_db_connection
from app.core.settings_service import get_setting
import app.core.log_service as log_service
from app.core.blender_runner import BlenderRunner
import app.core.ffmpeg_runner as ffmpeg_runner
import app.core.notification_service as notification_service
from app.core.project_scanner import sanitize_folder_name

class RenderQueue(QThread):
    # Signals for UI updates
    job_started = Signal(int, str)  # job_id, label
    job_progress = Signal(int, int) # job_id, percent
    job_log = Signal(int, str)      # job_id, log_line
    job_finished = Signal(int, str, str) # job_id, status (Completed/Failed), output_file
    queue_state_changed = Signal(str) # Running, Paused, Stopped
    job_stats = Signal(int, dict)   # job_id, stats (memory, tiles, samples, remaining)

    def __init__(self):
        super().__init__()
        self.state = "Stopped"  # Running, Paused, Stopped
        self.current_runner = None
        self.current_job_id = None
        self._is_running = True

    def run(self):
        log_service.info("Hilo de la cola de renderizado iniciado.")
        
        while self._is_running:
            if self.state == "Stopped":
                self.msleep(200)
                continue
                
            if self.state == "Paused":
                self.msleep(500)
                continue
                
            # State is "Running": fetch next Pending job
            job = self._get_next_pending_job()
            if not job:
                # No more jobs, finish queue execution
                log_service.info("Todos los trabajos de la cola han finalizado.")
                self.state = "Stopped"
                self.queue_state_changed.emit("Stopped")
                self._handle_completion_action()
                continue
                
            # Process the job
            self.current_job_id = job["id"]
            self._process_job(job)
            self.current_job_id = None
            
        log_service.info("Hilo de la cola de renderizado finalizado.")

    def start_queue(self):
        if self.state != "Running":
            was_paused = (self.state == "Paused")
            self.state = "Running"
            self.queue_state_changed.emit("Running")
            log_service.info("Cola de renderizado INICIADA.")
            if was_paused and self.current_runner:
                self.current_runner.resume()

    def pause_queue(self):
        if self.state == "Running":
            self.state = "Paused"
            self.queue_state_changed.emit("Paused")
            log_service.info("Cola de renderizado PAUSADA.")
            if self.current_runner:
                self.current_runner.pause()

    def stop_queue(self):
        self.state = "Stopped"
        self.queue_state_changed.emit("Stopped")
        log_service.info("Cola de renderizado DETENIDA.")
        self.cancel_current_job()

    def cancel_current_job(self):
        if self.current_runner:
            self.current_runner.cancel()

    def stop_thread(self):
        self._is_running = False
        self.stop_queue()
        self.wait()

    def _get_next_pending_job(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT j.*, p.project_code, p.blend_path as proj_path
            FROM jobs j
            JOIN projects p ON j.project_id = p.id
            WHERE j.status = 'Pending'
            ORDER BY j.priority DESC, j.id ASC
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        return row

    def _update_job_status(self, job_id, status, error_summary=None, output_file=None, start_time=None, finish_time=None, duration=None, log_file=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        updates = ["status = ?"]
        params = [status]
        
        if error_summary is not None:
            updates.append("error_summary = ?")
            params.append(error_summary)
        if output_file is not None:
            updates.append("output_file = ?")
            params.append(output_file)
        if log_file is not None:
            updates.append("log_file = ?")
            params.append(log_file)
        if start_time is not None:
            updates.append("started_at = ?")
            params.append(start_time)
        if finish_time is not None:
            updates.append("finished_at = ?")
            params.append(finish_time)
        if duration is not None:
            updates.append("duration_seconds = ?")
            params.append(duration)
            
        params.append(job_id)
        cursor.execute(f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        conn.close()

    def _resolve_paths(self, job):
        """Resolves auto-incremented, non-overwriting versions for output files."""
        project_code = job["project_code"]
        camera_name = job["camera_name"] or "Camera"
        profile = job["profile"] or "Client"
        output_root = job["output_root"]
        
        safe_cam = sanitize_folder_name(camera_name)
        profile_lower = profile.lower()
        
        # 1. Output directory routing (Backward compatibility match with existing folders)
        match = re.search(r'camara[_ ]+(.*)', camera_name, re.IGNORECASE)
        cam_id = match.group(1).strip() if match else safe_cam
        
        posibles_carpetas = [cam_id, f"Camara {cam_id}", camera_name, safe_cam]
        carpeta_destino = safe_cam
        for pc in posibles_carpetas:
            safe_pc = sanitize_folder_name(pc)
            if os.path.isdir(os.path.join(output_root, safe_pc)):
                carpeta_destino = safe_pc
                break
                
        cam_dir = os.path.abspath(os.path.join(output_root, carpeta_destino))
        root_dir = os.path.abspath(output_root)
        if not cam_dir.startswith(root_dir):
            raise ValueError(f"Ruta de destino fuera del directorio del proyecto: {cam_dir}")
            
        os.makedirs(cam_dir, exist_ok=True)
        
        # Determine format extension
        ext = "png"
        if profile == "Draft":
            ext = "jpg"
            
        # 2. Find next version index depending on naming style
        naming_style = get_setting("naming_style", "professional")
        
        version = 1
        while True:
            if naming_style == "simple":
                version_str = f"{version:02d}"
                filename = f"{version_str}.{ext}"
                video_filename = f"{version_str}.mp4"
            else:
                version_str = f"v{version:03d}"
                filename = f"{project_code}_{safe_cam}_{profile_lower}_{version_str}.{ext}"
                video_filename = f"{project_code}_{safe_cam}_montaje_{version_str}.mp4"
                
            full_path = os.path.join(cam_dir, filename)
            
            # Check if file already exists
            if not os.path.exists(full_path):
                # Also check montage/video path to avoid collision
                if naming_style == "simple":
                    montage_filename = f"{version_str}.jpg"
                else:
                    montage_filename = f"{project_code}_{safe_cam}_montaje_{version_str}.jpg"
                    
                montage_path = os.path.join(cam_dir, montage_filename)
                anim_dir = os.path.join(cam_dir, version_str)
                
                if not os.path.exists(full_path) and not os.path.exists(montage_path) and not os.path.exists(anim_dir):
                    break
            version += 1
            
        if naming_style == "simple":
            version_str = f"{version:02d}"
            filename = f"{version_str}.{ext}"
            montage_filename = f"{version_str}.jpg"
            video_filename = f"{version_str}.mp4"
        else:
            version_str = f"v{version:03d}"
            filename = f"{project_code}_{safe_cam}_{profile_lower}_{version_str}.{ext}"
            montage_filename = f"{project_code}_{safe_cam}_montaje_{version_str}.jpg"
            video_filename = f"{project_code}_{safe_cam}_montaje_{version_str}.mp4"

        # Resolve target files
        if job["job_type"] == "SINGLE_CAMERA_ANIMATION":
            anim_dir = os.path.join(cam_dir, version_str)
            os.makedirs(anim_dir, exist_ok=True)
            render_pattern = os.path.join(anim_dir, "####")
            final_output = os.path.join(cam_dir, video_filename)
            return render_pattern, final_output, version_str
        else:
            full_path = os.path.join(cam_dir, filename)
            montage_path = os.path.join(cam_dir, montage_filename)
            return full_path, montage_path, version_str

    def _process_job(self, job):
        job_id = job["id"]
        project_code = job["project_code"]
        camera_name = job["camera_name"] or "Camera"
        job_type = job["job_type"]
        
        label = f"{project_code} - {camera_name} ({job['profile']})"
        log_service.info(f"Iniciando trabajo [{job_id}]: {label}", project_code)
        
        start_time_raw = datetime.datetime.now()
        start_time_str = start_time_raw.strftime("%Y-%m-%d %H:%M:%S")
        self._update_job_status(job_id, "Running", start_time=start_time_str)
        self.job_started.emit(job_id, label)
        
        # 1. Resolve output paths dynamically
        render_path, secondary_path, version_str = self._resolve_paths(job)
        
        # Initialize Runner
        self.current_runner = BlenderRunner(project_code, job_id, camera_name)
        self._update_job_status(job_id, "Running", log_file=self.current_runner.log_path)
        
        # Connect runner logs and progress to queue signals
        self.current_runner.log_received.connect(lambda line: self.job_log.emit(job_id, line))
        self.current_runner.progress_changed.connect(lambda pct: self.job_progress.emit(job_id, pct))
        self.current_runner.render_stats_received.connect(lambda stats: self.job_stats.emit(job_id, stats))
        
        # Execution status state variables
        self_retcode = None
        self_err = ""
        
        def on_runner_finished(retcode, err):
            nonlocal self_retcode, self_err
            self_retcode = retcode
            self_err = err
            
        self.current_runner.finished.connect(on_runner_finished)
        
        # 2. Trigger Render based on Job Type
        target_blend = job.get("blend_path") or job.get("output_pattern")
        if job_type == "SINGLE_CAMERA_STILL":
            self.current_runner.run_still_render(
                blend_path=target_blend,
                camera_name=camera_name,
                output_path=render_path,
                profile=job["profile"],
                res_pct=job["resolution_percent"],
                device="GPU",
                frame=job["frame_start"]
            )
        elif job_type == "SINGLE_CAMERA_ANIMATION":
            self.current_runner.run_animation_render(
                blend_path=target_blend,
                camera_name=camera_name,
                output_path=render_path, # folder/vXXX/####
                frame_start=job["frame_start"],
                frame_end=job["frame_end"],
                profile=job["profile"],
                res_pct=job["resolution_percent"],
                device="GPU"
            )
            
        # Wait for render to complete (runner runs synchronously in this QThread)
        while self_retcode is None:
            self.msleep(100)
            
        # Clean up runner reference
        self.current_runner = None
        
        # 3. Handle Rendering Results
        finish_time_raw = datetime.datetime.now()
        finish_time_str = finish_time_raw.strftime("%Y-%m-%d %H:%M:%S")
        duration = (finish_time_raw - start_time_raw).total_seconds()
        
        if self_retcode == 0:
            # Render succeeded!
            if job_type == "SINGLE_CAMERA_ANIMATION" and job.get("include_postprocessing", 1) == 0:
                final_output_file = os.path.dirname(render_path)
            else:
                final_output_file = render_path
            
            # Postprocessing / Montages
            # A. If it was a Still frame and has Montage configured
            # Look up if the snapshot has a montage path
            conn = get_db_connection()
            snapshot = conn.execute("SELECT * FROM snapshots WHERE id = ?", (job["snapshot_id"],)).fetchone()
            conn.close()
            
            montage_blend = ""
            if snapshot:
                # In project_scanner we resolved the montage path if it exists
                # Let's search if there is a _montaje.blend file in the same folder as the blend file
                blend_dir = os.path.dirname(snapshot["blend_path"])
                stem = os.path.splitext(os.path.basename(snapshot["blend_path"]))[0]
                possible_montage = os.path.join(blend_dir, f"{stem}_montaje.blend")
                if os.path.exists(possible_montage):
                    montage_blend = possible_montage
            
            if job_type == "SINGLE_CAMERA_STILL" and montage_blend and job.get("include_postprocessing", 1) == 1:
                self.job_started.emit(job_id, f"Montando imagen: {camera_name}")
                log_service.info(f"Iniciando render de montaje final usando: {montage_blend}", project_code)
                
                self.current_runner = BlenderRunner(project_code, job_id, camera_name + "_montaje")
                self.current_runner.log_received.connect(lambda line: self.job_log.emit(job_id, line))
                self.current_runner.progress_changed.connect(lambda pct: self.job_progress.emit(job_id, 50 + int(pct/2))) # scaled 50-100%
                self.current_runner.render_stats_received.connect(lambda stats: self.job_stats.emit(job_id, stats))
                
                montage_retcode = None
                montage_err = ""
                
                def on_montage_finished(retcode, err):
                    nonlocal montage_retcode, montage_err
                    montage_retcode = retcode
                    montage_err = err
                    
                self.current_runner.finished.connect(on_montage_finished)
                
                self.current_runner.run_montage_render(
                    montage_blend_path=montage_blend,
                    img_path=render_path,
                    output_path=secondary_path # JPEG output file
                )
                
                while montage_retcode is None:
                    self.msleep(100)
                    
                self.current_runner = None
                if montage_retcode == 0:
                    final_output_file = secondary_path
                else:
                    log_service.error(f"El montaje falló: {montage_err}. Se conserva render base.", project_code)
            
            # B. If it was an Animation sequence, compile video with FFmpeg
            elif job_type == "SINGLE_CAMERA_ANIMATION" and job.get("include_postprocessing", 1) == 1:
                self.job_started.emit(job_id, f"Compilando video: {camera_name}")
                fps = snapshot["fps"] if snapshot else 24
                fps_base = snapshot["fps_base"] if snapshot else 1
                
                # Blender output will have frame numbers like C:\\renders\\Cam_A\\v001\\0001.png
                # Build pattern for FFmpeg
                anim_pattern = os.path.join(os.path.dirname(render_path), "####.png")
                
                success, ffmpeg_err = ffmpeg_runner.compile_video(
                    image_pattern=anim_pattern,
                    output_path=secondary_path, # mp4 file
                    fps=fps,
                    fps_base=fps_base
                )
                
                if success:
                    final_output_file = secondary_path
                else:
                    log_service.error(f"Fallo al compilar video con FFmpeg: {ffmpeg_err}", project_code)
            
            # Validation checks
            is_valid = True
            fail_reason = ""
            
            if not os.path.exists(final_output_file):
                is_valid = False
                fail_reason = f"El archivo de salida esperado no se generó: {os.path.basename(final_output_file)}"
            elif not os.path.isdir(final_output_file) and os.path.getsize(final_output_file) == 0:
                is_valid = False
                fail_reason = f"El archivo de salida está vacío (0 bytes): {os.path.basename(final_output_file)}"
                
            if is_valid:
                # Update database to Completed
                self._update_job_status(
                    job_id, "Completed",
                    output_file=final_output_file,
                    finish_time=finish_time_str,
                    duration=duration
                )
                self.job_finished.emit(job_id, "Completed", final_output_file)
                log_service.info(f"Trabajo [{job_id}] COMPLETADO en {duration:.1f} segundos.", project_code)
                
                # Generate preview thumbnail
                thumb_path = os.path.join(os.path.dirname(final_output_file), ".previews", os.path.basename(final_output_file) + "_thumb.jpg")
                has_thumb = False
                if job_type == "SINGLE_CAMERA_STILL":
                    has_thumb = ffmpeg_runner.generate_thumbnail(final_output_file, thumb_path)
                elif job_type == "SINGLE_CAMERA_ANIMATION":
                    # Make thumbnail from the first frame of sequence
                    first_frame_file = render_path.replace("####", f"{job['frame_start']:04d}")
                    if os.path.exists(first_frame_file):
                        has_thumb = ffmpeg_runner.generate_thumbnail(first_frame_file, thumb_path)
                
                # Send Success Notification
                duration_minutes = int(duration / 60)
                duration_seconds = int(duration % 60)
                time_str = f"{duration_minutes}m {duration_seconds}s" if duration_minutes > 0 else f"{duration_seconds}s"
                
                notif_msg = (
                    f"✅ *Render finalizado*\n"
                    f"*Proyecto:* {project_code}\n"
                    f"*Cámara:* {camera_name}\n"
                    f"*Perfil:* {job['profile']}\n"
                    f"*Tiempo:* {time_str}\n"
                    f"*Archivo:* `{os.path.basename(final_output_file)}`"
                )
                
                notification_service.send_notification(
                    text=notif_msg,
                    image_path=thumb_path if has_thumb else None
                )
            else:
                log_service.error(f"Trabajo [{job_id}] falló validación post-render: {fail_reason}", project_code)
                self_retcode = -3
                self_err = fail_reason
            
        else:
            # Render failed or cancelled
            if self_retcode == -2:
                # Cancelled by user
                self._update_job_status(job_id, "Cancelled", error_summary="Cancelado por el usuario", finish_time=finish_time_str)
                self.job_finished.emit(job_id, "Cancelled", "")
                log_service.warning(f"Trabajo [{job_id}] CANCELADO por el usuario.", project_code)
            else:
                # System Error
                retry_count = job["retry_count"]
                max_retries = job["max_retries"]
                
                if retry_count < max_retries:
                    # Retry Job
                    new_retry = retry_count + 1
                    log_service.warning(f"Trabajo [{job_id}] falló. Reintentando ({new_retry}/{max_retries})...", project_code)
                    
                    conn = get_db_connection()
                    conn.execute("UPDATE jobs SET status = 'Pending', retry_count = ? WHERE id = ?", (new_retry, job_id))
                    conn.commit()
                    conn.close()
                    
                    self.job_finished.emit(job_id, "Pending", "")
                else:
                    # Mark as Failed
                    self._update_job_status(
                        job_id, "Failed",
                        error_summary=self_err,
                        finish_time=finish_time_str,
                        duration=duration
                    )
                    self.job_finished.emit(job_id, "Failed", "")
                    log_service.error(f"Trabajo [{job_id}] FALLIDO. Error: {self_err}", project_code)
                    
                    # Send failure notification
                    notif_msg = (
                        f"❌ *Render fallido*\n"
                        f"*Proyecto:* {project_code}\n"
                        f"*Cámara:* {camera_name}\n"
                        f"*Error:* {self_err}\n"
                        f"Se continuará con el siguiente trabajo de la cola."
                    )
                    notification_service.send_notification(text=notif_msg)

    def _handle_completion_action(self):
        """Executes completion actions like shutdown or suspend."""
        action = get_setting("shutdown_on_complete", "none")
        if action == "none":
            return
            
        log_service.info(f"Ejecutando acción de finalización de cola: {action}")
        
        if action == "shutdown":
            # Shutdown Windows safely (60 seconds delay to allow logs/notifications to finish)
            os.system("shutdown /s /t 60 /c \"IP Blender Tool ha finalizado todos los renders.\"")
        elif action == "sleep":
            # Suspend Windows (requires rundll32)
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
