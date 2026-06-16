import os
import datetime

APPDATA = os.environ.get("APPDATA")
if not APPDATA:
    APPDATA = os.path.expanduser("~")
LOG_DIR = os.path.join(APPDATA, "IP Blender Tool", "logs")

# Listeners that want to receive real-time log updates (e.g. GUI console)
_log_listeners = []

def register_log_listener(callback):
    """Registers a callback function to receive all log messages."""
    if callback not in _log_listeners:
        _log_listeners.append(callback)

def unregister_log_listener(callback):
    """Unregisters a log callback."""
    if callback in _log_listeners:
        _log_listeners.remove(callback)

def _write_log(level, project_code, message):
    os.makedirs(LOG_DIR, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] [{level}] {message}"
    
    # Send to stdout
    print(formatted_msg)
    
    # Notify GUI listeners
    for listener in _log_listeners:
        try:
            listener(formatted_msg)
        except Exception:
            pass
            
    # Write to project file if project_code is provided
    proj = project_code if project_code else "system"
    today = datetime.date.today().strftime("%Y-%m-%d")
    log_file = os.path.join(LOG_DIR, f"render_{proj}_{today}.log")
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(formatted_msg + "\n")
    except Exception as e:
        print(f"Failed to write to log file {log_file}: {e}")

def info(message, project_code=None):
    _write_log("INFO", project_code, message)

def warning(message, project_code=None):
    _write_log("WARNING", project_code, message)

def error(message, project_code=None):
    _write_log("ERROR", project_code, message)
