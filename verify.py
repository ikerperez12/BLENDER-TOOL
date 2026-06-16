import sys
import os

print("=== IP BLENDER TOOL VERIFICATION SCRIPT ===")
print(f"Running on Python version: {sys.version}")
print(f"Current Directory: {os.getcwd()}")

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 1. Check module imports
print("\n[1/4] Verifying imports...")
try:
    import PySide6
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QThread
    print("  SUCCESS: PySide6 imported successfully.")
except ImportError as e:
    print(f"  FAILED: PySide6 import error: {e}")
    sys.exit(1)

try:
    import psutil
    print("  SUCCESS: psutil imported successfully.")
except ImportError as e:
    print(f"  FAILED: psutil import error: {e}")
    sys.exit(1)

try:
    import requests
    print("  SUCCESS: requests imported successfully.")
except ImportError as e:
    print(f"  FAILED: requests import error: {e}")
    sys.exit(1)

# 2. Check Database init
print("\n[2/4] Verifying database configuration...")
try:
    from app.core.db import init_db, get_db_connection, DB_PATH
    init_db()
    
    # Assert database is in AppData Roaming
    assert "AppData" in DB_PATH and "Roaming" in DB_PATH, f"Database path not in AppData Roaming: {DB_PATH}"
    print(f"  SUCCESS: Database initialized at AppData: {DB_PATH}")
    
    conn = get_db_connection()
    # Check journal mode
    res = conn.execute("PRAGMA journal_mode;").fetchone()[0]
    print(f"  SUCCESS: Database journal mode: {res}")
    
    # Check tables
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    print(f"  SUCCESS: Detected database tables: {', '.join(tables)}")
    conn.close()
except Exception as e:
    print(f"  FAILED: Database verification failed: {e}")
    sys.exit(1)

# 3. Check Settings Auto-detect
print("\n[3/4] Verifying Settings & Auto-detection...")
try:
    from app.core.settings_service import get_setting, auto_detect_blender, auto_detect_ffmpeg
    blender = get_setting("blender_path")
    ffmpeg = get_setting("ffmpeg_path")
    base_dir = get_setting("base_dir")
    
    print(f"  Setting 'base_dir': {base_dir}")
    print(f"  Setting 'blender_path': {blender}")
    print(f"  Setting 'ffmpeg_path': {ffmpeg}")
    
    detected_blender = auto_detect_blender()
    detected_ffmpeg = auto_detect_ffmpeg()
    print(f"  Auto-detected Blender: {detected_blender}")
    print(f"  Auto-detected FFmpeg: {detected_ffmpeg}")
    
    if not blender:
        print("  WARNING: Blender path is empty. User must set it in GUI Settings.")
    elif not os.path.exists(blender) and blender != "blender":
        print(f"  WARNING: Configured Blender path does not exist: {blender}")
        
except Exception as e:
    print(f"  FAILED: Settings verification failed: {e}")
    sys.exit(1)

# 4. Check Blender Scripts existence
print("\n[4/4] Verifying internal script files...")
script_files = [
    "blender_scripts/scan_scene.py",
    "blender_scripts/render_camera.py",
    "blender_scripts/update_compositor.py"
]
all_scripts_exist = True
for path in script_files:
    if os.path.exists(path):
        print(f"  SUCCESS: File exists: {path}")
    else:
        print(f"  FAILED: File missing: {path}")
        all_scripts_exist = False

if not all_scripts_exist:
    sys.exit(1)

print("\n=== ALL SYSTEM SANITY CHECKS PASSED SUCCESSFULLY ===")
