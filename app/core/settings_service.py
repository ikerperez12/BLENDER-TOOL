import os
import glob
import subprocess
import sys
from app.core.db import get_db_connection

def get_base_dir():
    """Returns the base application directory, supporting PyInstaller freezing."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json

def _get_default_docs():
    """Dynamically locates the standard user Documents/Documentos folder, including OneDrive fallbacks."""
    home = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    possible_paths = [
        os.path.join(home, "OneDrive", "Documentos"),
        os.path.join(home, "OneDrive", "Documents"),
        os.path.join(home, "Documentos"),
        os.path.join(home, "Documents"),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return os.path.join(home, "Documents")

DEFAULT_DOCS = _get_default_docs()

DEFAULT_PROFILES = {
    "IP Legacy": {
        "mode": "IP_LEGACY",
        "projects_root": DEFAULT_DOCS,
        "renders_root": "",
        "project_folder_pattern": "({project_id})*",
        "blend_folder_pattern": "03_{project_id}_3D_BLENDER",
        "renders_folder_pattern": "06_{project_id}_3D_RENDERS",
        "camera_file_pattern": "*Camara*.blend",
        "montage_suffix": "_montaje"
    },
    "Manual": {
        "mode": "MANUAL_FOLDER",
        "projects_root": DEFAULT_DOCS,
        "renders_root": ""
    },
    "Single Blend": {
        "mode": "SINGLE_BLEND",
        "renders_root": ""
    }
}

DEFAULT_SETTINGS = {
    "base_dir": DEFAULT_DOCS,  # Default base path, configurable
    "blender_path": "",
    "ffmpeg_path": "ffmpeg",
    "telegram_enabled": False,
    "telegram_token": "",
    "telegram_chat_id": "",
    "discord_enabled": False,
    "discord_webhook": "",
    "shutdown_on_complete": "none",  # none, shutdown, sleep
    "naming_style": "professional",  # professional, simple
    "first_run_completed": False,
    "active_mode": "IP_LEGACY",       # IP_LEGACY, MANUAL_FOLDER, SINGLE_BLEND
    "projects_root": DEFAULT_DOCS,
    "renders_root": "",
    "settings_schema_version": 1,
    "app_version": "1.0.0",
    "active_profile": "IP Legacy",
    "profiles": json.dumps(DEFAULT_PROFILES),
}

def get_setting(key, default=None):
    """Retrieves a setting value from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    
    if row is not None:
        return row[0]
    
    if default is not None:
        return default
    return DEFAULT_SETTINGS.get(key, "")

def set_setting(key, value):
    """Saves a setting value to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, str(value))
    )
    conn.commit()
    conn.close()

def get_setting_bool(key, default=False):
    """Helper to retrieve settings as boolean values safely."""
    val = get_setting(key)
    if val == "":
        return default
    return str(val).lower() in ("true", "1", "yes")

def get_active_profile_name():
    """Returns the name of the active configuration profile."""
    return get_setting("active_profile", "IP Legacy")

def get_profiles():
    """Loads all profiles from the JSON settings string."""
    profiles_json = get_setting("profiles", "")
    if not profiles_json:
        return DEFAULT_PROFILES
    try:
        return json.loads(profiles_json)
    except Exception:
        return DEFAULT_PROFILES

def set_profiles(profiles_dict):
    """Saves all profiles to the JSON settings string."""
    set_setting("profiles", json.dumps(profiles_dict))

def get_active_profile_setting(key, default=None):
    """Gets a specific setting inside the active profile."""
    active_profile = get_active_profile_name()
    profiles = get_profiles()
    profile = profiles.get(active_profile, {})
    return profile.get(key, default)

def set_active_profile_setting(key, value):
    """Sets a specific setting inside the active profile and saves it."""
    active_profile = get_active_profile_name()
    profiles = get_profiles()
    if active_profile not in profiles:
        profiles[active_profile] = {}
    profiles[active_profile][key] = value
    set_profiles(profiles)

def auto_detect_blender():
    """Tries to find the highest installed version of Blender."""
    # 1. Check standard Program Files path
    base_path = "C:\\Program Files\\Blender Foundation"
    if os.path.exists(base_path):
        subdirs = glob.glob(os.path.join(base_path, "Blender *"))
        if subdirs:
            # Sort subfolders to find the latest version (e.g. Blender 5.1 over 4.2)
            subdirs.sort(reverse=True)
            for sdir in subdirs:
                exe_path = os.path.join(sdir, "blender.exe")
                if os.path.exists(exe_path):
                    return exe_path
                    
    # 2. Check if 'blender' is in the PATH
    try:
        subprocess.run(["where", "blender"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return "blender"
    except Exception:
        pass
        
    return ""

def auto_detect_ffmpeg():
    """Tries to find ffmpeg across common Windows installation locations."""
    # 1. Check if 'ffmpeg' is already in PATH
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            startupinfo=startupinfo, check=True, timeout=10
        )
        return "ffmpeg"
    except Exception:
        pass

    home = os.environ.get("USERPROFILE", os.path.expanduser("~"))

    # 2. Common installation directories on Windows
    search_paths = [
        # WinGet packages
        os.path.join(home, r"AppData\Local\Microsoft\WinGet\Packages"),
        # Chocolatey
        r"C:\ProgramData\chocolatey\bin",
        r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin",
        # Scoop
        os.path.join(home, r"scoop\apps\ffmpeg\current\bin"),
        os.path.join(home, r"scoop\shims"),
        # Manual installs in common locations
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
        r"C:\Program Files (x86)\ffmpeg\bin",
        os.path.join(home, r"ffmpeg\bin"),
        os.path.join(home, r"Downloads\ffmpeg\bin"),
        os.path.join(home, r"Desktop\ffmpeg\bin"),
    ]

    for search_dir in search_paths:
        if not os.path.exists(search_dir):
            continue
        # Direct check
        exe_path = os.path.join(search_dir, "ffmpeg.exe")
        if os.path.isfile(exe_path):
            return exe_path
        # Recursive glob (1 level deep for WinGet-style nested packages)
        matches = glob.glob(os.path.join(search_dir, "**/ffmpeg.exe"), recursive=True)
        if matches:
            return matches[0]

    return ""


def is_ffmpeg_available(ffmpeg_path=None):
    """Tests if a given ffmpeg path (or the saved setting) actually works."""
    if ffmpeg_path is None:
        ffmpeg_path = get_setting("ffmpeg_path", "")
    if not ffmpeg_path:
        return False
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(
            [ffmpeg_path, "-version"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            startupinfo=startupinfo, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False

def initialize_settings():
    """Detects paths if empty and populates settings table with defaults."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if we need to insert settings
    for key, def_val in DEFAULT_SETTINGS.items():
        cursor.execute("SELECT 1 FROM settings WHERE key = ?", (key,))
        if not cursor.fetchone():
            val = def_val
            if key == "blender_path":
                val = auto_detect_blender()
            elif key == "ffmpeg_path":
                val = auto_detect_ffmpeg()
            cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, val))
            
    conn.commit()
    conn.close()

# Note: initialize_settings is called inside init_db to prevent table-not-found race conditions on import.
