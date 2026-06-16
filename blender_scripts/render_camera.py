import bpy
import sys
import argparse
import os

def parse_args():
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
    
    return parser.parse_args(args_list)

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
    scene = bpy.context.scene
    
    # 1. Set active camera
    if args.camera in bpy.data.objects:
        scene.camera = bpy.data.objects[args.camera]
        print(f"Setting active camera to: {args.camera}")
    else:
        print(f"Error: Camera '{args.camera}' not found in blend file!")
        sys.exit(1)
        
    # 2. Configure output path and format
    # Force output directory exists
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
    print(f"Resolution percentage: {args.res_pct}%")
    
    # 4. Configure Engine
    if args.engine:
        scene.render.engine = args.engine
    engine = scene.render.engine
    print(f"Render engine: {engine}")
    
    # 5. Configure Device
    if engine == 'CYCLES':
        configure_cycles_device(args.device)
        
    # 6. Apply profile
    apply_profile(args.profile, engine)
    
    # 7. Configure frames
    scene.frame_start = args.frame_start
    scene.frame_end = args.frame_end
    
    # 8. Start render
    print("---RENDER_START---")
    if args.is_animation:
        # For animations, we let Blender handle the frame range
        bpy.ops.render.render(animation=True, write_still=True)
    else:
        # For still frames, we render the current frame
        scene.frame_current = args.frame_start
        bpy.ops.render.render(write_still=True)
    print("---RENDER_END---")

if __name__ == "__main__":
    render()
