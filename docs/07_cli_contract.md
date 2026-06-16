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
