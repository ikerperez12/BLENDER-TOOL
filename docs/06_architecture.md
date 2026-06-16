# System Architecture - IP Blender Tool

This document describes the component relationships, MVC layout, and multi-threaded design of **IP Blender Tool**.

---

## 🗺️ Component Relationships

```mermaid
graph TD
    UI[PySide6 UI main_window.py] -->|1. Ingest Code| Scanner[project_scanner.py]
    Scanner -->|2. Run metadata scan| ScanScript[scan_scene.py]
    ScanScript -->|3. Save Snapshot| SQLite[(SQLite Roaming DB)]
    UI -->|4. Push Jobs| SQLite
    UI -->|5. Control Queue| Queue[render_queue.py QThread]
    Queue -->|6. Fetch Job| SQLite
    Queue -->|7. Launch Render| Runner[blender_runner.py]
    Runner -->|8. Run background CLI| RenderScript[render_camera.py]
    Runner -->|9. Swaps composites| CompScript[update_compositor.py]
    Queue -->|10. Compile / Thumb| FFmpeg[ffmpeg_runner.py]
    Queue -->|11. Push notification| Outbox[notification_service.py Queue]
    Outbox -->|12. Dispatch async webhook| Web[Telegram / Discord Webhooks]
```

---

## 🧵 Multi-Threading Model

To ensure the user interface remains completely fluid during long rendering sessions, execution is distributed across distinct threads and processes:

### 1. Main UI Thread (PySide6 Event Loop)
- Handles widget rendering, table updates, and user interactions.
- Receives thread-safe Qt Signals from background workers to update progress bars and append logs.
- Never runs heavy file operations or subprocess executions.

### 2. Render Queue Thread (`QThread`)
- Runs a sequential loop in the background.
- Queries SQLite for `Pending` tasks.
- Spawns the `BlenderRunner` and waits synchronously for its return code. This blocks the background thread but leaves the UI thread untouched.

### 3. Subprocesses (CLI execution)
- Spawns standalone `blender.exe` and `ffmpeg.exe` instances.
- Operates in separate OS-level process trees, preventing Blender GUI-related crashes from impacting the management application.

### 4. Notification Outbox Thread (Daemon Thread)
- Consumes a FIFO thread-safe queue.
- Dispatches HTTP requests using connection poolings.
- Has a strict 5-second timeout to isolate rendering operations from network latency.
