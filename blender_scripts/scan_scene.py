import bpy
import json
import os
import sys

def scan():
    # Gather cameras
    cameras = []
    active_cam = bpy.context.scene.camera
    for obj in bpy.data.objects:
        if obj.type == 'CAMERA':
            cameras.append({
                "name": obj.name,
                "active": (active_cam is not None and obj.name == active_cam.name)
            })

    # Render settings
    scene = bpy.context.scene
    render = scene.render

    # Check for missing textures/assets
    missing_assets = []
    for img in bpy.data.images:
        if img.source == 'FILE':
            abs_path = bpy.path.abspath(img.filepath)
            # Normalize path for comparison
            if abs_path and not os.path.exists(abs_path):
                missing_assets.append({
                    "name": img.name,
                    "filepath": img.filepath,
                    "resolved_path": abs_path
                })

    # Build metadata dictionary
    metadata = {
        "blend_file": bpy.data.filepath,
        "scenes": [s.name for s in bpy.data.scenes],
        "current_scene": scene.name,
        "cameras": cameras,
        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
        "fps": render.fps,
        "fps_base": render.fps_base,
        "engine": render.engine,
        "resolution_x": render.resolution_x,
        "resolution_y": render.resolution_y,
        "resolution_percentage": render.resolution_percentage,
        "missing_assets": missing_assets
    }

    # Print scan result wrapped in tags
    print("---SCAN_RESULT_START---")
    print(json.dumps(metadata, indent=2))
    print("---SCAN_RESULT_END---")

if __name__ == "__main__":
    scan()
