import os
import subprocess
import zipfile
import json
import datetime
import shutil
from app.core.db import get_db_connection, DB_PATH
from app.core.settings_service import get_setting

def run_preflight_checks():
    """Runs a system-wide preflight diagnostics scan."""
    results = {
        "blender": {"ok": False, "version": "No detectado", "err": ""},
        "ffmpeg": {"ok": False, "version": "No detectado", "err": ""},
        "db": {"ok": False, "path": DB_PATH, "err": ""},
        "permissions": {"ok": False, "err": ""}
    }

    # 1. Check Blender
    blender_bin = get_setting("blender_path")
    if not blender_bin:
        results["blender"]["err"] = "La ruta de Blender no está configurada."
    else:
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            r = subprocess.run(
                [blender_bin, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore",
                startupinfo=startupinfo
            )
            if r.returncode == 0:
                # Extract first line (e.g. Blender 5.1.0)
                first_line = r.stdout.splitlines()[0]
                results["blender"]["ok"] = True
                results["blender"]["version"] = first_line
            else:
                results["blender"]["err"] = f"Código de retorno de Blender: {r.returncode}"
        except Exception as e:
            results["blender"]["err"] = str(e)

    # 2. Check FFmpeg
    ffmpeg_bin = get_setting("ffmpeg_path", "ffmpeg")
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        r = subprocess.run(
            [ffmpeg_bin, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
            startupinfo=startupinfo
        )
        if r.returncode == 0:
            first_line = r.stdout.splitlines()[0]
            results["ffmpeg"]["ok"] = True
            results["ffmpeg"]["version"] = first_line
        else:
            results["ffmpeg"]["err"] = f"Código de retorno de FFmpeg: {r.returncode}"
    except Exception as e:
        results["ffmpeg"]["err"] = str(e)

    # 3. Check SQLite DB
    try:
        conn = get_db_connection()
        journal = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        conn.close()
        results["db"]["ok"] = True
        results["db"]["err"] = f"Modo Journal: {journal}"
    except Exception as e:
        results["db"]["err"] = str(e)

    # 4. Check folder write permissions
    base_dir = get_setting("base_dir")
    if not os.path.exists(base_dir):
        results["permissions"]["err"] = f"El directorio base de proyectos no existe: {base_dir}"
    else:
        try:
            test_file = os.path.join(base_dir, ".ipbt_write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            results["permissions"]["ok"] = True
        except Exception as e:
            results["permissions"]["err"] = f"Sin permisos de escritura en {base_dir}: {e}"

    return results

def export_diagnostics_zip(output_path, include_database=False):
    """Exports logs, redacted settings, and database tables to a troubleshooting ZIP."""
    import re
    import sqlite3
    import shutil
    
    appdata_dir = os.path.join(os.environ.get("APPDATA", ""), "IP Blender Tool")
    logs_dir = os.path.join(appdata_dir, "logs")
    db_file_path = os.path.join(appdata_dir, "jobs.sqlite")
    
    # 1. Fetch and redact settings
    redacted_settings = {}
    try:
        conn = get_db_connection()
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        conn.close()
        for r in rows:
            k, v = r["key"], r["value"]
            if any(secret in k.lower() for secret in ["token", "chat_id", "webhook"]):
                redacted_settings[k] = "[REDACTED_SECRET]"
            elif v and ("Users\\" in v or "Users/" in v):
                # Anonymize paths containing username
                v_clean = re.sub(r'Users[\\/][^\\/]+', 'Users\\<USER>', v)
                redacted_settings[k] = v_clean
            else:
                redacted_settings[k] = v
    except Exception as e:
        redacted_settings["error"] = f"Fallo al leer ajustes: {e}"

    temp_settings_file = os.path.join(os.environ.get("TEMP", ""), "ipbt_settings_redacted.json")
    with open(temp_settings_file, "w", encoding="utf-8") as f:
        json.dump(redacted_settings, f, indent=2)

    temp_db_file = None
    if include_database and os.path.exists(db_file_path):
        temp_db_file = os.path.join(os.environ.get("TEMP", ""), "ipbt_jobs_sanitized.sqlite")
        try:
            shutil.copy(db_file_path, temp_db_file)
            # Open the copied database to sanitize it
            conn = sqlite3.connect(temp_db_file)
            cursor = conn.cursor()
            
            # Redact secrets in settings table
            cursor.execute("UPDATE settings SET value = '[REDACTED_SECRET]' WHERE key LIKE '%token%' OR key LIKE '%chat_id%' OR key LIKE '%webhook%'")
            
            # Redact user paths in settings table
            cursor.execute("SELECT key, value FROM settings")
            for key, val in cursor.fetchall():
                if val and ("Users\\" in val or "Users/" in val):
                    val_clean = re.sub(r'Users[\\/][^\\/]+', 'Users\\<USER>', val)
                    cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (val_clean, key))
                    
            # Anonymize projects paths
            cursor.execute("SELECT id, blend_path, output_path, project_root, selected_blend_file, renders_root FROM projects")
            for pid, bp, op, pr, sbf, rr in cursor.fetchall():
                bp_clean = re.sub(r'Users[\\/][^\\/]+', 'Users\\<USER>', bp) if bp else bp
                op_clean = re.sub(r'Users[\\/][^\\/]+', 'Users\\<USER>', op) if op else op
                pr_clean = re.sub(r'Users[\\/][^\\/]+', 'Users\\<USER>', pr) if pr else pr
                sbf_clean = re.sub(r'Users[\\/][^\\/]+', 'Users\\<USER>', sbf) if sbf else sbf
                rr_clean = re.sub(r'Users[\\/][^\\/]+', 'Users\\<USER>', rr) if rr else rr
                cursor.execute("""
                    UPDATE projects 
                    SET blend_path = ?, output_path = ?, project_root = ?, selected_blend_file = ?, renders_root = ?
                    WHERE id = ?
                """, (bp_clean, op_clean, pr_clean, sbf_clean, rr_clean, pid))
                
            # Anonymize jobs paths
            cursor.execute("SELECT id, output_root, output_pattern, blend_path, output_file, error_summary FROM jobs")
            for jid, oroot, opat, bpath, outfile, err_sum in cursor.fetchall():
                oroot_clean = re.sub(r'Users[\\/][^\\/]+', 'Users\\<USER>', oroot) if oroot else oroot
                opat_clean = re.sub(r'Users[\\/][^\\/]+', 'Users\\<USER>', opat) if opat else opat
                bpath_clean = re.sub(r'Users[\\/][^\\/]+', 'Users\\<USER>', bpath) if bpath else bpath
                outfile_clean = re.sub(r'Users[\\/][^\\/]+', 'Users\\<USER>', outfile) if outfile else outfile
                err_sum_clean = re.sub(r'Users[\\/][^\\/]+', 'Users\\<USER>', err_sum) if err_sum else err_sum
                cursor.execute("""
                    UPDATE jobs 
                    SET output_root = ?, output_pattern = ?, blend_path = ?, output_file = ?, error_summary = ?
                    WHERE id = ?
                """, (oroot_clean, opat_clean, bpath_clean, outfile_clean, err_sum_clean, jid))
                
            conn.commit()
            conn.close()
        except Exception as e:
            log_service.error(f"Fallo al sanitizar la copia de la base de datos: {e}")
            temp_db_file = None

    # 2. Package everything in a ZIP
    try:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add redacted settings
            zipf.write(temp_settings_file, "settings_redacted.json")
            
            # Add database schema dump (not rows, for privacy)
            sqlite_dump = []
            try:
                conn = get_db_connection()
                schemas = conn.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL").fetchall()
                conn.close()
                sqlite_dump = [r["sql"] for r in schemas]
            except Exception as e:
                sqlite_dump = [f"Fallo al leer esquema: {e}"]
                
            temp_schema_file = os.path.join(os.environ.get("TEMP", ""), "ipbt_db_schema.sql")
            with open(temp_schema_file, "w", encoding="utf-8") as f:
                f.write("\n\n".join(sqlite_dump))
                
            zipf.write(temp_schema_file, "db_schema.sql")

            # Add system logs
            if os.path.exists(logs_dir):
                for root, _, files in os.walk(logs_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Store in ZIP under logs/ directory
                        arcname = os.path.join("logs", file)
                        zipf.write(file_path, arcname)

            # Add system pre-flight checks
            preflight = run_preflight_checks()
            temp_preflight_file = os.path.join(os.environ.get("TEMP", ""), "ipbt_preflight.json")
            with open(temp_preflight_file, "w", encoding="utf-8") as f:
                json.dump(preflight, f, indent=2)
            zipf.write(temp_preflight_file, "preflight_diagnostics.json")

            # Add database if requested and sanitization succeeded
            if temp_db_file and os.path.exists(temp_db_file):
                zipf.write(temp_db_file, "jobs_sanitized.sqlite")

        # Clean up temp files
        files_to_clean = [temp_settings_file, temp_schema_file, temp_preflight_file]
        if temp_db_file:
            files_to_clean.append(temp_db_file)
            
        for f in files_to_clean:
            try:
                os.remove(f)
            except Exception:
                pass
        return True, ""
    except Exception as e:
        return False, str(e)

def create_demo_project():
    """Generates a fully functional offline demo project using Blender CLI in background."""
    from app.core.settings_service import get_setting, get_active_profile_setting
    base_dir = get_active_profile_setting("projects_root") or get_setting("base_dir")
    blender_bin = get_setting("blender_path")
    
    # Check if Blender is available and exists
    blender_ok = bool(blender_bin and os.path.exists(blender_bin))
    
    demo_dir = os.path.join(base_dir, "(0000)_Proyecto_Demo")
    blend_dir = os.path.join(demo_dir, "03_0000_3D_BLENDER")
    renders_dir = os.path.join(demo_dir, "06_0000_3D_RENDERS")
    
    try:
        os.makedirs(blend_dir, exist_ok=True)
        os.makedirs(renders_dir, exist_ok=True)
        
        # 1. Write the README_DEMO.md
        readme_path = os.path.join(demo_dir, "LEEME_DEMO.txt")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("===============================================\n")
            f.write("       PROYECTO DEMO - IP BLENDER TOOL\n")
            f.write("===============================================\n\n")
            f.write("Este proyecto demo ha sido generado automáticamente de forma 100% offline.\n\n")
            if not blender_ok:
                f.write("⚠️ ATENCIÓN: No se detectó Blender durante la generación de este demo.\n")
                f.write("Por lo tanto, solo se ha creado la estructura de carpetas y este archivo de ayuda.\n")
                f.write("Para generar los archivos .blend de demo, configura la ruta de Blender en la app y vuelve a generar el demo.\n\n")
            f.write("Estructura:\n")
            f.write("- 03_0000_3D_BLENDER/: Contiene los archivos blend de la escena y el montaje.\n")
            f.write("- 06_0000_3D_RENDERS/: Es la carpeta destino donde se guardarán los resultados.\n\n")
            f.write("Cómo probarlo:\n")
            f.write("1. Escribe '0000' en el campo Nº Proyecto de la pantalla principal de la app.\n")
            f.write("2. Pulsa el botón Escanear Carpeta.\n")
            f.write("3. Selecciona 'Camara A' y haz click en 'Añadir a Cola'.\n")
            f.write("4. Pulsa 'Iniciar Renderizado'.\n")
        
        if not blender_ok:
            return True, "partial_no_blender"
            
        # 2. Write inline python command to let Blender generate the .blend files
        blender_py_expr = (
            "import bpy\n"
            "import os\n"
            "# 1. Setup Camera A\n"
            "if 'Camera' in bpy.data.objects:\n"
            "    bpy.data.objects['Camera'].name = 'Camara A'\n"
            "bpy.ops.wm.save_as_mainfile(filepath=r'" + os.path.join(blend_dir, "(0000)_Camara A.blend") + "')\n"
            "# 2. Setup Montage composite file\n"
            "bpy.context.scene.use_nodes = True\n"
            "tree = bpy.context.scene.node_tree\n"
            "for n in tree.nodes: tree.nodes.remove(n)\n"
            "img_node = tree.nodes.new('CompositorNodeImage')\n"
            "img = bpy.data.images.new('render.png', width=128, height=128)\n"
            "img_node.image = img\n"
            "comp_node = tree.nodes.new('CompositorNodeComposite')\n"
            "tree.links.new(img_node.outputs['Image'], comp_node.inputs['Image'])\n"
            "bpy.ops.wm.save_as_mainfile(filepath=r'" + os.path.join(blend_dir, "(0000)_Camara A_montaje.blend") + "')\n"
        )
        
        temp_py = os.path.join(os.environ.get("TEMP", ""), "ipbt_demo_gen.py")
        with open(temp_py, "w", encoding="utf-8") as f:
            f.write(blender_py_expr)
            
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        # Run Blender to execute script
        cmd = [blender_bin, "-b", "--python", temp_py]
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        
        try:
            os.remove(temp_py)
        except Exception:
            pass
            
        if r.returncode != 0:
            return False, f"Blender falló al compilar la demo (Código {r.returncode})"
            
        return True, demo_dir
    except Exception as e:
        return False, str(e)
