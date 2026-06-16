import os
import glob
import subprocess
import json
import re
import datetime
from app.core.db import get_db_connection
from app.core.settings_service import get_setting, get_base_dir
import app.core.log_service as log_service

def sanitize_folder_name(name):
    """Sanitizes folder/camera names safely for Windows filesystems."""
    name = name.strip()
    # Replace characters not allowed in file names
    name = re.sub(r'[<>:"/\\|?*]+', "_", name)
    name = re.sub(r'\s+', "_", name)
    # Allow alphanumeric, underscores, hyphens, and dots
    name = re.sub(r'[^\w\-\.]+', "_", name, flags=re.UNICODE)
    name = name.strip("._ ")
    
    if not name:
        name = "unnamed"
        
    reserved = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }
    if name.upper() in reserved:
        name = f"_{name}"
        
    return name[:80]

def locate_project_folder(project_code):
    """Finds the project folder inside the configured base directory."""
    base_dir = get_setting("base_dir")
    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"El directorio base no existe: {base_dir}")

    # 1. Search for glob matching f"({project_code})*" as in legacy prototype
    pattern = os.path.join(base_dir, f"({project_code})*")
    matches = glob.glob(pattern)
    if matches:
        return matches[0]

    # 2. Fallback check for directories containing the project code (e.g. "0024")
    for entry in os.scandir(base_dir):
        if entry.is_dir() and project_code in entry.name:
            return entry.path

    # 3. Fallback search recursive 1-level deep
    for entry in os.scandir(base_dir):
        if entry.is_dir():
            for subentry in os.scandir(entry.path):
                if subentry.is_dir() and project_code in subentry.name:
                    return subentry.path

    raise FileNotFoundError(f"No se encontró la carpeta del proyecto '{project_code}' en {base_dir}")

def run_blender_scan(blend_path):
    """Runs blender in background with scan_scene.py and parses JSON output."""
    blender_bin = get_setting("blender_path")
    is_demo = "0000" in os.path.basename(blend_path)
    blender_exists = blender_bin and os.path.exists(blender_bin)
    
    if is_demo and not blender_exists:
        log_service.warning("Ejecutando escaneo simulado para el Proyecto Demo (Blender no configurado).")
        filename = os.path.basename(blend_path)
        
        if "Salon" in filename or "Salon" in blend_path:
            return {
                "blend_file": blend_path,
                "scenes": ["Escena Salon"],
                "current_scene": "Escena Salon",
                "cameras": [
                    {"name": "Camara A", "active": True},
                    {"name": "Camara B", "active": False},
                    {"name": "Camara C", "active": False}
                ],
                "frame_start": 1,
                "frame_end": 1,
                "fps": 24,
                "fps_base": 1,
                "engine": "CYCLES_MOCK",
                "resolution_x": 1920,
                "resolution_y": 1080,
                "resolution_percent": 100,
                "resolution_percentage": 100,
                "missing_assets": []
            }
        elif "Exterior" in filename or "Exterior" in blend_path:
            return {
                "blend_file": blend_path,
                "scenes": ["Escena Exterior"],
                "current_scene": "Escena Exterior",
                "cameras": [
                    {"name": "Camara Terraza", "active": True},
                    {"name": "Camara Jardin", "active": False}
                ],
                "frame_start": 1,
                "frame_end": 24,
                "fps": 24,
                "fps_base": 1,
                "engine": "CYCLES_MOCK",
                "resolution_x": 1920,
                "resolution_y": 1080,
                "resolution_percent": 100,
                "resolution_percentage": 100,
                "missing_assets": []
            }
        else:
            return {
                "blend_file": blend_path,
                "scenes": ["Escena Demo"],
                "current_scene": "Escena Demo",
                "cameras": [
                    {"name": "Camara A", "active": True},
                    {"name": "Camara B", "active": False}
                ],
                "frame_start": 1,
                "frame_end": 1,
                "fps": 24,
                "fps_base": 1,
                "engine": "CYCLES_MOCK",
                "resolution_x": 1920,
                "resolution_y": 1080,
                "resolution_percent": 100,
                "resolution_percentage": 100,
                "missing_assets": []
            }

    if not blender_bin:
         raise FileNotFoundError("La ruta de Blender no está configurada en los ajustes.")

    script_path = os.path.join(
        get_base_dir(),
        "blender_scripts",
        "scan_scene.py"
    )

    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script de escaneo no encontrado en: {script_path}")

    log_service.info(f"Escaneando archivo: {os.path.basename(blend_path)}")
    
    cmd = [blender_bin, "-b", blend_path, "--python-exit-code", "1", "--python", script_path]
    
    # Run subprocess safely
    startupinfo = None
    if os.name == 'nt':
        # Prevent CMD window from popping up on Windows
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
            startupinfo=startupinfo,
            timeout=120
        )
    except subprocess.TimeoutExpired:
        log_service.error(f"El escaneo de Blender superó el tiempo límite (120s) para: {blend_path}")
        raise RuntimeError(
            "Blender tardó demasiado en responder (timeout de 120 segundos).\n"
            "El archivo .blend podría estar corrupto, ser extremadamente grande o requerir mucha memoria.\n"
            "Prueba a revisar el archivo directamente en Blender o a usar el Modo Carpeta Manual."
        )
    
    if result.returncode != 0:
        log_service.error(f"Error al ejecutar escaneo de Blender. Código: {result.returncode}\nStderr: {result.stderr}")
        raise RuntimeError(f"Blender falló al escanear el archivo (Código {result.returncode})")

    # Extract JSON between tags
    stdout = result.stdout
    match = re.search(r"---SCAN_RESULT_START---(.*?)---SCAN_RESULT_END---", stdout, re.DOTALL)
    if not match:
        log_service.error(f"No se encontró salida JSON en la respuesta de Blender.\nStdout: {stdout}")
        raise RuntimeError("No se pudo obtener información del archivo blend (salida JSON no encontrada).")

    try:
        data = json.loads(match.group(1).strip())
        return data
    except json.JSONDecodeError as e:
        log_service.error(f"Fallo al decodificar JSON: {e}\nTexto: {match.group(1)}")
        raise RuntimeError("JSON corrupto devuelto por Blender.")

def scan_project(identifier, mode="IP_LEGACY", custom_output_dir=None):
    """
    Scans a project (under one of three modes: IP_LEGACY, MANUAL_FOLDER, SINGLE_BLEND),
    discovers blend files, runs scans, stores in database, and returns the project id
    and found jobs metadata.
    """
    log_service.info(f"Escaneando proyecto en modo {mode}: {identifier}")
    
    if mode == "IP_LEGACY":
        proj_dir = locate_project_folder(identifier)
        project_code = identifier
        
        # Resolve output directory
        output_dir = glob.glob(os.path.join(proj_dir, "*_3D_RENDERS*"))
        if output_dir:
            out_path = output_dir[0]
        else:
            out_path = os.path.join(proj_dir, "06_" + project_code + "_3D_RENDERS")
            
        # Find blend files
        blend_files = []
        dirs_3d = glob.glob(os.path.join(proj_dir, "*_3D_BLENDER*"))
        if not dirs_3d:
            # Fallback to recursively listing all .blend files in the project folder
            for root, dirs, files in os.walk(proj_dir):
                depth = root[len(proj_dir):].count(os.sep)
                if depth > 3:
                    continue
                for f in files:
                    if f.endswith(".blend") and not f.startswith("."):
                        blend_files.append(os.path.join(root, f))
        else:
            for d in dirs_3d:
                for f in os.listdir(d):
                    if f.endswith(".blend") and not f.startswith("."):
                        blend_files.append(os.path.join(d, f))
                        
    elif mode == "MANUAL_FOLDER":
        if not os.path.exists(identifier) or not os.path.isdir(identifier):
            raise FileNotFoundError(f"El directorio especificado no existe o no es una carpeta: {identifier}")
        proj_dir = identifier
        
        # Determine project code based on folder name, ensure unique
        base_code = os.path.basename(proj_dir)
        if not base_code:
            base_code = "carpeta_manual"
        project_code = base_code
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT blend_path FROM projects WHERE project_code = ?", (project_code,))
        row = cursor.fetchone()
        if row and row[0] != proj_dir:
            i = 1
            while True:
                candidate = f"{base_code}_{i}"
                cursor.execute("SELECT blend_path FROM projects WHERE project_code = ?", (candidate,))
                if not cursor.fetchone():
                    project_code = candidate
                    break
                i += 1
        conn.close()
        
        if custom_output_dir:
            out_path = custom_output_dir
        else:
            # Look for folder with "render" in the name
            renders_dirs = [entry.path for entry in os.scandir(proj_dir) if entry.is_dir() and "render" in entry.name.lower()]
            if renders_dirs:
                out_path = renders_dirs[0]
            else:
                out_path = os.path.join(proj_dir, "renders")
        
        blend_files = []
        for root, dirs, files in os.walk(proj_dir):
            depth = root[len(proj_dir):].count(os.sep)
            if depth > 3:
                continue
            for f in files:
                if f.endswith(".blend") and not f.startswith("."):
                    blend_files.append(os.path.join(root, f))
                    
    elif mode == "SINGLE_BLEND":
        if not os.path.exists(identifier) or not os.path.isfile(identifier) or not identifier.endswith(".blend"):
            raise FileNotFoundError(f"El archivo especificado no existe o no es un archivo .blend válido: {identifier}")
        proj_dir = os.path.dirname(identifier)
        
        # Determine project code based on blend file name
        blend_name = os.path.splitext(os.path.basename(identifier))[0]
        project_code = blend_name
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT blend_path FROM projects WHERE project_code = ?", (project_code,))
        row = cursor.fetchone()
        if row and row[0] != identifier:
            i = 1
            while True:
                candidate = f"{blend_name}_{i}"
                cursor.execute("SELECT blend_path FROM projects WHERE project_code = ?", (candidate,))
                if not cursor.fetchone():
                    project_code = candidate
                    break
                i += 1
        conn.close()
        
        if custom_output_dir:
            out_path = custom_output_dir
        else:
            out_path = os.path.join(proj_dir, "renders")
            
        blend_files = [identifier]
        
    else:
        raise ValueError(f"Modo de escaneo no válido: {mode}")

    if not blend_files:
        raise FileNotFoundError("No se encontraron archivos .blend.")
        
    log_service.info(f"Carpeta/archivo origen: {proj_dir}")
    log_service.info(f"Directorio de renders resuelto: {out_path}")
    
    # Save project in database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    project_root = proj_dir
    selected_blend_file = identifier if mode == "SINGLE_BLEND" else ""
    renders_root_val = custom_output_dir or ""
    profile_name = "IP Legacy" if mode == "IP_LEGACY" else ("Manual" if mode == "MANUAL_FOLDER" else "Single Blend")
    
    cursor.execute("""
        INSERT OR REPLACE INTO projects (
            project_code, blend_path, output_path, project_mode,
            project_root, selected_blend_file, renders_root, profile_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        project_code, 
        identifier if mode == "SINGLE_BLEND" else proj_dir, 
        out_path, 
        mode,
        project_root, 
        selected_blend_file, 
        renders_root_val, 
        profile_name
    ))
    
    # Get project_id
    cursor.execute("SELECT id FROM projects WHERE project_code = ?", (project_code,))
    project_id = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    # Group main blends and montages
    main_blends = []
    montage_blends = {}
    
    if mode == "SINGLE_BLEND":
        main_blends = [identifier]
        # Check for corresponding montage
        stem = os.path.splitext(os.path.basename(identifier))[0]
        montage_path = os.path.join(proj_dir, f"{stem}_montaje.blend")
        if os.path.exists(montage_path):
            montage_blends[stem] = montage_path
    else:
        for f in blend_files:
            stem = os.path.splitext(os.path.basename(f))[0]
            if stem.endswith("_montaje"):
                base_stem = stem[:-8]
                montage_blends[base_stem] = f
            else:
                main_blends.append(f)
                
    scanned_snapshots = []
    
    for blend_path in main_blends:
        file_size = os.path.getsize(blend_path)
        mod_time = os.path.getmtime(blend_path)
        
        try:
            metadata = run_blender_scan(blend_path)
            
            # Check if there is a corresponding montage
            stem = os.path.splitext(os.path.basename(blend_path))[0]
            montage_path = montage_blends.get(stem, "")
            
            warnings = []
            if metadata.get("missing_assets"):
                warnings.append(f"Faltan {len(metadata['missing_assets'])} texturas/assets.")
                
            warnings_str = " | ".join(warnings) if warnings else ""
            
            # Save snapshot to SQLite
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO snapshots (
                    project_id, blend_path, blend_size, blend_modified_at, blender_version,
                    scene_name, fps, fps_base, resolution_x, resolution_y,
                    resolution_percent, render_engine, scan_warnings, frame_start, frame_end
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_id, blend_path, file_size, mod_time, "5.1",
                metadata["current_scene"], metadata["fps"], metadata["fps_base"],
                metadata["resolution_x"], metadata["resolution_y"],
                metadata["resolution_percentage"], metadata["engine"], warnings_str,
                metadata.get("frame_start", 1), metadata.get("frame_end", 1)
            ))
            snapshot_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            metadata["snapshot_id"] = snapshot_id
            metadata["montage_path"] = montage_path
            metadata["blend_path"] = blend_path
            metadata["output_path"] = out_path
            # Keep compatibility with existing code
            metadata["blend_file"] = blend_path 
            
            scanned_snapshots.append(metadata)
        except Exception as e:
            log_service.error(f"Fallo al escanear {blend_path}: {e}", project_code)
            
    return project_id, scanned_snapshots
