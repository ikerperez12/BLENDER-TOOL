import bpy
import sys
import argparse
import os

def parse_args():
    if "--" in sys.argv:
        args_list = sys.argv[sys.argv.index("--") + 1:]
    else:
        args_list = []

    parser = argparse.ArgumentParser(description="Update compositor nodes with a render image and render final montage.")
    parser.add_argument("--img-path", type=str, required=True, help="Path to the source PNG image render.")
    parser.add_argument("--output", type=str, required=True, help="Path to save the resulting montage JPEG.")
    
    return parser.parse_args(args_list)

def update_and_render():
    args = parse_args()
    
    print(f"Montage - Input Image: {args.img_path}")
    print(f"Montage - Output Path: {args.output}")

    # 1. Update all image data blocks that reference a PNG
    updated_any = False
    for img in bpy.data.images:
        if img.source == 'FILE' and ('.png' in img.name.lower() or '.png' in img.filepath.lower()):
            img.filepath = args.img_path
            img.reload()
            updated_any = True
            print(f"Updated image datablock: {img.name} -> {args.img_path}")

    # 2. Update Image nodes in compositor nodes explicitly
    if bpy.context.scene.use_nodes and bpy.context.scene.node_tree:
        for node in bpy.context.scene.node_tree.nodes:
            if node.type == 'IMAGE':
                if node.image:
                    node.image.filepath = args.img_path
                    node.image.reload()
                    updated_any = True
                    print(f"Updated Compositor Image Node: {node.name} with {args.img_path}")

    if not updated_any:
        print("Warning: No PNG image datablocks or compositor Image nodes were found to swap!")

    # 3. Force outputs path
    out_dir = os.path.dirname(args.output)
    os.makedirs(out_dir, exist_ok=True)
    
    bpy.context.scene.render.filepath = args.output
    
    # Set format based on extension (usually JPEG)
    ext = os.path.splitext(args.output)[1].lower()
    if ext in ('.jpg', '.jpeg'):
        bpy.context.scene.render.image_settings.file_format = 'JPEG'
    else:
        bpy.context.scene.render.image_settings.file_format = 'PNG'

    # Render montage frame 1
    bpy.context.scene.frame_current = 1
    
    print("---MONTAGE_RENDER_START---")
    bpy.ops.render.render(write_still=True)
    print("---MONTAGE_RENDER_END---")

if __name__ == "__main__":
    update_and_render()
