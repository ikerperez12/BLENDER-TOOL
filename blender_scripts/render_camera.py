import bpy
import sys
import argparse
import os
import time
import json
import re

def emit_event(event_type, **payload):
    payload["type"] = event_type
    payload["timestamp"] = time.time()
    print("IPBT_EVENT " + json.dumps(payload, ensure_ascii=False), flush=True)

# Global args to reference inside handlers
render_args = None

@bpy.app.handlers.persistent
def on_render_pre(scene):
    emit_event("frame_started", phase="render", frame=scene.frame_current)

@bpy.app.handlers.persistent
def on_render_write(scene):
    total = 1
    if render_args:
        total = render_args.frame_end - render_args.frame_start + 1
    frame_idx = scene.frame_current
    if render_args:
        frame_idx = scene.frame_current - render_args.frame_start + 1
    emit_event("frame_done", phase="render", frame=frame_idx, total_frames=total, output=scene.render.filepath)

@bpy.app.handlers.persistent
def on_render_stats(scene):
    stats_str = scene.render.stats
    m = re.search(r"Sample\s+(\d+)\s*/\s*(\d+)", stats_str)
    if m:
        current_sample = int(m.group(1))
        total_samples = int(m.group(2))
        emit_event("progress_update", phase="render", current=current_sample, total=total_samples, stats=stats_str)

# Notify launch immediately when python script starts executing
emit_event("job_started", phase="launch", message="Blender iniciado")

def parse_args():
    global render_args
    # Find '--' in argv and parse arguments after it
    if "--" in sys.argv:
        args_list = sys.argv[sys.argv.index("--") + 1:]
    else:
        args_list = []

    parser = argparse.ArgumentParser(description="Render a specific camera from a blend file.")
    parser.add_argument("--camera", type=str, required=True, help="Name of the camera to render.")
    parser.add_argument("--output", type=str, required=True, help="Full path of the output file.")
    parser.add_argument("--profile", type=str, default="Client", choices=["Draft", "Client", "Final"], help="Render quality profile.")
    parser.add_argument("--res-pct", type=int, default=100, help="Resolution percentage.")
    parser.add_argument("--engine", type=str, default="", help="Override render engine (CYCLES, EEVEE, BLENDER_WORKBENCH).")
    parser.add_argument("--device", type=str, default="GPU", choices=["CPU", "GPU", "AUTO"], help="Render device.")
    parser.add_argument("--frame-start", type=int, default=1, help="Start frame.")
    parser.add_argument("--frame-end", type=int, default=1, help="End frame.")
    parser.add_argument("--is-animation", action="store_true", help="Render as animation instead of single frame.")
    
    parsed = parser.parse_args(args_list)
    render_args = parsed
    return parsed

def configure_cycles_device(device_mode):
    """Configures GPU/CPU rendering for Cycles."""
    if device_mode == "CPU":
        bpy.context.scene.cycles.device = 'CPU'
        return

    # Try to configure GPU
    try:
        preferences = bpy.context.preferences
        addons = preferences.addons
        cycles_preferences = addons['cycles'].preferences
        
        # Determine available GPU backends
        device_types = ['OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL']
        gpu_backend = None
        
        for d_type in device_types:
            cycles_preferences.compute_device_type = d_type
            cycles_preferences.get_devices()
            devices = cycles_preferences.devices
            if any(d.type in ('CUDA', 'OPTIX', 'HIP', 'ONEAPI', 'METAL') for d in devices):
                gpu_backend = d_type
                break
        
        if gpu_backend:
            cycles_preferences.compute_device_type = gpu_backend
            # Enable all devices
            for device in cycles_preferences.devices:
                device.use = True
            bpy.context.scene.cycles.device = 'GPU'
            print(f"Cycles configured for GPU: {gpu_backend}")
        else:
            bpy.context.scene.cycles.device = 'CPU'
            print("No compatible GPU found. Defaulting to CPU.")
    except Exception as e:
        print(f"Error configuring GPU device: {e}. Defaulting to CPU.")
        bpy.context.scene.cycles.device = 'CPU'

def apply_profile(profile_name, engine):
    """Applies quality settings based on profile."""
    scene = bpy.context.scene
    
    if engine == 'CYCLES':
        if profile_name == "Draft":
            scene.cycles.samples = 32
            scene.cycles.use_denoise = False
            # Optimize bounces for speed
            scene.cycles.max_bounces = 4
            scene.cycles.diffuse_bounces = 2
            scene.cycles.glossy_bounces = 2
            scene.cycles.transmission_bounces = 2
        elif profile_name == "Client":
            scene.cycles.samples = 256
            scene.cycles.use_denoise = True
            scene.cycles.max_bounces = 12
        elif profile_name == "Final":
            scene.cycles.samples = 1024
            scene.cycles.use_denoise = True
            scene.cycles.max_bounces = 16
    else:  # EEVEE
        # In Blender 4.2+, Eevee uses different property names (EEVEE_NEXT)
        is_legacy = not hasattr(scene, "eevee") or not hasattr(scene.eevee, "ray_tracing")
        if profile_name == "Draft":
            if hasattr(scene, "eevee"):
                if hasattr(scene.eevee, "taa_render_samples"):
                    scene.eevee.taa_render_samples = 16
                elif hasattr(scene.eevee, "render_samples"):
                    scene.eevee.render_samples = 16
        elif profile_name == "Client":
            if hasattr(scene, "eevee"):
                if hasattr(scene.eevee, "taa_render_samples"):
                    scene.eevee.taa_render_samples = 64
                elif hasattr(scene.eevee, "render_samples"):
                    scene.eevee.render_samples = 64
        elif profile_name == "Final":
            if hasattr(scene, "eevee"):
                if hasattr(scene.eevee, "taa_render_samples"):
                    scene.eevee.taa_render_samples = 128
                elif hasattr(scene.eevee, "render_samples"):
                    scene.eevee.render_samples = 128

def render():
    args = parse_args()
    emit_event("blend_loaded", phase="load", message=f"Archivo .blend cargado: {os.path.basename(bpy.data.filepath)}")
    
    scene = bpy.context.scene
    
    # 1. Set active camera
    if args.camera in bpy.data.objects:
        scene.camera = bpy.data.objects[args.camera]
        print(f"Setting active camera to: {args.camera}")
    else:
        emit_event("error", code="CAMERA_NOT_FOUND", message=f"No se encontró la cámara '{args.camera}' en la escena.")
        sys.exit(1)
        
    # 2. Configure output path and format
    out_dir = os.path.dirname(args.output)
    os.makedirs(out_dir, exist_ok=True)
    
    scene.render.filepath = args.output
    
    # Set format based on extension
    ext = os.path.splitext(args.output)[1].lower()
    if ext in ('.jpg', '.jpeg'):
        scene.render.image_settings.file_format = 'JPEG'
    elif ext == '.exr':
        scene.render.image_settings.file_format = 'OPEN_EXR'
    else:
        scene.render.image_settings.file_format = 'PNG'
        
    # 3. Configure Resolution percentage
    scene.render.resolution_percentage = args.res_pct
    
    # 4. Configure Engine
    if args.engine:
        scene.render.engine = args.engine
    engine = scene.render.engine
    
    # 5. Configure Device
    if engine == 'CYCLES':
        configure_cycles_device(args.device)
        
    # 6. Apply profile
    apply_profile(args.profile, engine)
    
    # 7. Configure frames
    scene.frame_start = args.frame_start
    scene.frame_end = args.frame_end
    
    emit_event("scene_prepared", phase="prepare", message="Escena preparada correctamente")
    
    # Register handlers
    bpy.app.handlers.render_pre.append(on_render_pre)
    bpy.app.handlers.render_write.append(on_render_write)
    bpy.app.handlers.render_stats.append(on_render_stats)
    
    # 8. Start render
    emit_event("render_started", phase="render", message="Iniciando renderizado...")
    print("---RENDER_START---")
    
    if args.is_animation:
        bpy.ops.render.render(animation=True, write_still=True)
    else:
        scene.frame_current = args.frame_start
        bpy.ops.render.render(write_still=True)
        
    print("---RENDER_END---")
    
    emit_event("render_saved", phase="save", message=f"Archivo guardado: {os.path.basename(args.output)}")
    emit_event("job_completed", phase="complete", message="Render completado con éxito")

if __name__ == "__main__":
    render()
