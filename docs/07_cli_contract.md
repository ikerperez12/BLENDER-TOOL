# CLI Contracts - Blender subprocesses

This contract documents the CLI boundaries and stdout/JSON contracts between **IP Blender Tool** and background **Blender** processes.

---

## 🔍 1. Ingestion Scanner Contract

The scanner runs Blender in background mode, executing [scan_scene.py](file:///c:/PROYECTOS/IDEAS/BLENDER%20TOOL/blender_scripts/scan_scene.py):

```powershell
blender.exe -b "<blend_file_path>" --python-exit-code 1 --python "blender_scripts/scan_scene.py"
```

### Output JSON Schema
Stdout returns a JSON block wrapped between `---SCAN_RESULT_START---` and `---SCAN_RESULT_END---`:

```json
{
  "blend_file": "C:/path/to/project_0024.blend",
  "scenes": ["Interior", "Exterior"],
  "current_scene": "Interior",
  "cameras": [
    {"name": "Camara A", "active": true},
    {"name": "Camara B", "active": false}
  ],
  "frame_start": 1,
  "frame_end": 1,
  "fps": 24,
  "fps_base": 1,
  "engine": "CYCLES",
  "resolution_x": 1920,
  "resolution_y": 1080,
  "resolution_percentage": 100,
  "missing_assets": [
    {
      "name": "wood_diff.jpg",
      "filepath": "//textures/wood_diff.jpg",
      "resolved_path": "C:/path/textures/wood_diff.jpg"
    }
  ]
}
```

---

## 📷 2. Camera Rendering Contract

The runner runs Blender executing [render_camera.py](file:///c:/PROYECTOS/IDEAS/BLENDER%20TOOL/blender_scripts/render_camera.py):

```powershell
blender.exe -b "<blend_file_path>" --python-exit-code 1 --python "blender_scripts/render_camera.py" -- --camera "<cam_name>" --output "<out_path>" --profile "<Draft|Client|Final>" --res-pct <percentage> --device "<CPU|GPU|AUTO>" --frame-start <start> --frame-end <end> [--is-animation]
```

### Argument Schema
* `--camera`: Camera name found during ingestion.
* `--output`: Output render path.
* `--profile`: Settings profile determining samples and bounces.
* `--res-pct`: Render resolution override.
* `--device`: CYCLES GPU backend auto-detector.
* `--is-animation`: Enables animation frame sequences.

---

## 🖼️ 3. Montage Compositor Contract

The runner runs Blender executing [update_compositor.py](file:///c:/PROYECTOS/IDEAS/BLENDER%20TOOL/blender_scripts/update_compositor.py):

```powershell
blender.exe -b "<montage_blend_path>" --python-exit-code 1 --python "blender_scripts/update_compositor.py" -- --img-path "<rendered_png_path>" --output "<montage_jpeg_path>"
```
Loads the input PNG render, updates compositor nodes, re-renders the final composite frame 1, and saves it as a JPEG.

---

## 📡 4. Progress and State Event Logging Contract (IPBT_EVENT)

All Blender background scripts are required to output progress, state changes, warnings, and errors in a structured single-line log format prefixed with `IPBT_EVENT `.

### Log Line Syntax
```text
IPBT_EVENT {"type": "<event_type>", "phase": "<phase_name>", "message": "<log_message>", ...}
```
*Note: The script must flush stdout (`flush=True`) immediately after printing the event.*

### Phase Mappings
The pipeline execution is divided into the following phases:
* `launch`: Subprocess initialization.
* `load`: File loading.
* `prepare`: Setup scene parameters, camera overrides, rendering devices, and profiles.
* `render`: Active engine rendering loop.
* `save`: Post-processing, compositor operations, and file storage.
* `complete`: Graceful job completion.

### Event Types Schema

#### A. Execution Milestones
* **`job_started`**: Emitted on execution start.
  - Payload: `{"phase": "launch", "message": "..."}`
* **`blend_loaded`**: Emitted when the `.blend` file is fully loaded into memory.
  - Payload: `{"phase": "load", "message": "..."}`
* **`scene_prepared`**: Emitted when cameras, resolution overrides, and rendering configurations are successfully set up.
  - Payload: `{"phase": "prepare", "message": "..."}`
* **`render_started`**: Emitted just before calling the rendering operator.
  - Payload: `{"phase": "render", "message": "..."}`
* **`render_saved`**: Emitted when the rendered frame is saved.
  - Payload: `{"phase": "save", "message": "..."}`
* **`job_completed`**: Emitted on successful script exit.
  - Payload: `{"phase": "complete", "message": "..."}`

#### B. Progress Updates
* **`progress_update`**: Emitted periodically during a single frame render (primarily for Cycles samples progress).
  - Payload: `{"phase": "render", "current": int, "total": int}`
* **`frame_started`**: Emitted when beginning a specific frame.
  - Payload: `{"phase": "render", "frame": int}`
* **`frame_done`**: Emitted when a frame is saved during an animation sequence.
  - Payload: `{"phase": "render", "frame": int, "total_frames": int, "output": "..."}`

#### C. Diagnoses & Errors
* **`warning`**: Non-critical notices (e.g. missing texture file fallbacks).
  - Payload: `{"message": "..."}`
* **`error`**: Critical failures that halt execution.
  - Payload: `{"code": "<error_code>", "message": "..."}`
