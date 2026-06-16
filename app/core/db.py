import sqlite3
import os

# Roaming AppData path
APPDATA = os.environ.get("APPDATA")
if not APPDATA:
    APPDATA = os.path.expanduser("~")
DB_DIR = os.path.join(APPDATA, "IP Blender Tool")
DB_PATH = os.path.join(DB_DIR, "jobs.sqlite")

def get_db_connection():
    """Returns a connection configured with WAL and busy timeout."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    # Enable WAL mode for high concurrency
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Creates the tables if they do not exist."""
    import sqlite3
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Projects table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_code TEXT UNIQUE,
        blend_path TEXT,
        output_path TEXT,
        project_mode TEXT,
        project_root TEXT,
        selected_blend_file TEXT,
        renders_root TEXT,
        profile_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Run migrations for existing database if fields are missing
    columns_to_add = [
        ("project_mode", "TEXT"),
        ("project_root", "TEXT"),
        ("selected_blend_file", "TEXT"),
        ("renders_root", "TEXT"),
        ("profile_name", "TEXT")
    ]
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE projects ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            # Column already exists
            pass
    
    # 2. Snapshots table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        blend_path TEXT,
        blend_size INTEGER,
        blend_modified_at REAL,
        blender_version TEXT,
        scene_name TEXT,
        fps INTEGER,
        fps_base INTEGER,
        resolution_x INTEGER,
        resolution_y INTEGER,
        resolution_percent INTEGER,
        render_engine TEXT,
        scan_warnings TEXT,
        frame_start INTEGER DEFAULT 1,
        frame_end INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )
    """)
    
    # Run migration for existing databases for snapshots.frame_start
    try:
        cursor.execute("ALTER TABLE snapshots ADD COLUMN frame_start INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        # Column already exists
        pass

    # Run migration for existing databases for snapshots.frame_end
    try:
        cursor.execute("ALTER TABLE snapshots ADD COLUMN frame_end INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # 3. Jobs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        snapshot_id INTEGER,
        job_type TEXT,
        scene_name TEXT,
        camera_name TEXT,
        frame_start INTEGER,
        frame_end INTEGER,
        output_root TEXT,
        output_pattern TEXT, -- DEPRECATED: use blend_path instead
        blend_path TEXT,
        profile TEXT,
        resolution_percent INTEGER,
        status TEXT,
        priority INTEGER DEFAULT 0,
        retry_count INTEGER DEFAULT 0,
        max_retries INTEGER DEFAULT 2,
        started_at TIMESTAMP,
        finished_at TIMESTAMP,
        duration_seconds REAL,
        output_file TEXT,
        error_summary TEXT,
        log_file TEXT,
        include_postprocessing INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id),
        FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
    )
    """)
    
    # Run migration for existing databases for jobs.blend_path
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN blend_path TEXT")
    except sqlite3.OperationalError:
        # Column already exists
        pass

    # Run migration for existing databases for jobs.log_file
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN log_file TEXT")
    except sqlite3.OperationalError:
        # Column already exists
        pass
        
    # Run migration for existing databases for jobs.include_postprocessing
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN include_postprocessing INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # 4. Settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    
    # Reset any stuck 'Running' jobs from a previous interrupted session to 'Pending'
    cursor.execute("UPDATE jobs SET status = 'Pending' WHERE status = 'Running'")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
