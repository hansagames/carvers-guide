import bpy
import math
import bmesh
import mathutils
from pathlib import Path
from typing import Dict, Tuple, Optional
import argparse
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    "model_path": Path("model.glb").absolute(),
    "output_dir": Path("output").absolute(),
    "dpi": 300,
    "views": {
        "front": {"width": "width", "height": "height"},
        "back": {"width": "width", "height": "height"},
        "left": {"width": "depth", "height": "height"},
        "right": {"width": "depth", "height": "height"},
        "top": {"width": "width", "height": "depth"}
    },
    "lighting": {
        "key_light": {
            "type": "AREA",
            "energy": 800,
            "size": 50,
            "location": (100, -100, 100),
            "rotation": (math.radians(45), 0, math.radians(-45))
        },
        "fill_light": {
            "type": "AREA",
            "energy": 400,
            "size": 50,
            "location": (0, 100, 50),
            "rotation": (math.radians(60), 0, math.radians(180))
        },
        "rim_light": {
            "type": "AREA",
            "energy": 200,
            "size": 50,
            "location": (-100, -100, 100),
            "rotation": (math.radians(45), 0, math.radians(45))
        }
    },
    "material": {
        "color": (0.7, 0.7, 0.7, 1.0),
        "roughness": 0.5
    },
    "camera_views": {
        "front": ((0, 200, 0), (math.radians(90), 0, math.radians(180))),
        "back": ((0, -200, 0), (math.radians(90), 0, 0)),
        "left": ((200, 0, 0), (math.radians(90), 0, math.radians(90))),
        "right": ((-200, 0, 0), (math.radians(90), 0, math.radians(-90))),
        "top": ((0, 0, 200), (0, 0, 0))
    }
}

# Constants
METRIC_SCALE = 0.001  # Blender metric scale (mm)
WORLD_BG_COLOR = (0.8, 0.8, 0.8, 1.0)
WORLD_BG_STRENGTH = 0.5
MINIMUM_BLENDER_VERSION = (4, 0, 0)
SUPPORTED_EXTENSIONS = ('.glb', '.gltf')

def check_blender_version() -> None:
    """Ensure Blender version meets minimum requirements."""
    version = bpy.app.version
    if version < MINIMUM_BLENDER_VERSION:
        raise RuntimeError(f"Blender version {version} is unsupported. Requires {MINIMUM_BLENDER_VERSION} or higher.")
    logger.debug(f"Blender version {version} verified.")

def parse_arguments() -> Tuple[Path, Optional[float], Optional[float], Optional[float]]:
    """Parse and validate command-line arguments."""
    parser = argparse.ArgumentParser(description="Render orthographic views of a 3D model for printing.")
    parser.add_argument(
        "--model",
        type=Path,
        default=CONFIG["model_path"],
        help="Path to the input GLTF model file (.glb or .gltf)"
    )
    parser.add_argument(
        "--block-width",
        type=float,
        default=None,
        help="Block width in mm (X-axis)"
    )
    parser.add_argument(
        "--block-height",
        type=float,
        default=None,
        help="Block height in mm (Z-axis)"
    )
    parser.add_argument(
        "--block-depth",
        type=float,
        default=None,
        help="Block depth in mm (Y-axis)"
    )

    # Extract script arguments after '--'
    try:
        separator_index = sys.argv.index('--')
        script_args = sys.argv[separator_index + 1:]
    except ValueError:
        script_args = sys.argv[1:]

    args = parser.parse_args(script_args)

    # Validate model path
    if not args.model.exists():
        raise ValueError(f"Model file does not exist: {args.model}")
    if args.model.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Model file must be .glb or .gltf, got {args.model.suffix}")

    # Validate at least one dimension is provided
    if all(arg is None for arg in [args.block_width, args.block_height, args.block_depth]):
        raise ValueError("At least one of --block-width, --block-height, or --block-depth must be provided.")

    # Validate dimensions are positive
    for dim, value in [("width", args.block_width), ("height", args.block_height), ("depth", args.block_depth)]:
        if value is not None and value <= 0:
            raise ValueError(f"Block {dim} must be positive, got {value}")

    logger.info(f"Arguments: model={args.model}, width={args.block_width}, height={args.block_height}, depth={args.block_depth}")
    return args.model.absolute(), args.block_width, args.block_height, args.block_depth

def ensure_output_directory(output_dir: Path) -> None:
    """Create output directory if it doesn't exist."""
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Output directory: {output_dir}")

def clean_scene() -> None:
    """Clear scene and set metric units."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = METRIC_SCALE
    logger.debug("Scene cleared and set to metric units.")

def import_model(filepath: Path) -> bpy.types.Object:
    """Import GLTF model and return the first mesh object."""
    bpy.ops.import_scene.gltf(filepath=str(filepath))
    obj = next((obj for obj in bpy.context.selected_objects if obj.type == 'MESH'), None)
    if obj is None:
        raise ValueError("No mesh object found in the imported model.")
    logger.info(f"Imported model: {filepath}")
    return obj

def get_bounding_box(obj: bpy.types.Object) -> list[mathutils.Vector]:
    """Calculate world-space bounding box of an object."""
    return [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]

def center_and_align(
    obj: bpy.types.Object,
    target_dims: Optional[Dict[str, float]] = None
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Center and scale object to fit target dimensions, return target and scaled dimensions."""
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.location = (0, 0, 0)
    bpy.context.view_layer.update()

    # Calculate model bounding box
    bbox = get_bounding_box(obj)
    model_sizes = {
        "width": max(v.x for v in bbox) - min(v.x for v in bbox),
        "depth": max(v.y for v in bbox) - min(v.y for v in bbox),
        "height": max(v.z for v in bbox) - min(v.z for v in bbox)
    }

    # Validate non-zero model dimensions
    for dim, size in model_sizes.items():
        if size == 0:
            raise ValueError(f"Model {dim} is zero, cannot scale.")

    # Initialize target dimensions
    final_target_dims = {"width": None, "depth": None, "height": None}
    target_dims = target_dims or {}

    # Determine scale based on provided dimensions
    provided_dims = sum(1 for k, v in target_dims.items() if v is not None)
    if provided_dims == 0:
        final_target_dims = model_sizes.copy()
        scale = 1.0
    else:
        scales = [target_dims[dim] / model_sizes[dim] for dim in target_dims if target_dims[dim] is not None]
        scale = min(scales)
        for dim in ["width", "depth", "height"]:
            final_target_dims[dim] = target_dims.get(dim, model_sizes[dim] * scale)

    # Apply scaling and center
    obj.scale = (scale, scale, scale)
    bpy.context.view_layer.update()
    bpy.ops.object.transform_apply(scale=True)
    bbox = get_bounding_box(obj)
    center = sum(bbox, mathutils.Vector((0, 0, 0))) / 8.0
    obj.location = -center
    bpy.context.view_layer.update()

    scaled_dims = {key: size * scale for key, size in model_sizes.items()}
    logger.info(f"Scaled object. Target: {final_target_dims}, Scaled: {scaled_dims}")
    return final_target_dims, scaled_dims

def add_block_frame(dimensions: Dict[str, float]) -> None:
    """Add wireframe bounding box with specified dimensions."""
    mesh = bpy.data.meshes.new("block_frame")
    obj = bpy.data.objects.new("block_frame", mesh)
    bpy.context.scene.collection.objects.link(obj)
    
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bm.to_mesh(mesh)
    bm.free()
    
    obj.scale = (dimensions["width"] / 2, dimensions["depth"] / 2, dimensions["height"] / 2)
    obj.location = (0, 0, 0)
    obj.display_type = 'WIRE'
    obj.hide_render = True
    logger.debug("Added wireframe bounding box.")

def setup_lighting(config: Dict) -> None:
    """Configure scene lighting."""
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj)
    
    world = bpy.data.worlds["World"]
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = WORLD_BG_COLOR
    bg.inputs[1].default_value = WORLD_BG_STRENGTH

    for light_name, settings in config["lighting"].items():
        light_data = bpy.data.lights.new(name=light_name, type=settings["type"])
        light_data.energy = settings["energy"]
        light_data.size = settings["size"]
        light_obj = bpy.data.objects.new(name=light_name, object_data=light_data)
        light_obj.location = settings["location"]
        light_obj.rotation_euler = settings["rotation"]
        bpy.context.scene.collection.objects.link(light_obj)
    logger.debug("Lighting configured.")

def apply_material(obj: bpy.types.Object, material_config: Dict) -> None:
    """Apply high-contrast material to object."""
    if not obj.material_slots:
        mat = bpy.data.materials.new(name="PrintMaterial")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        output = nodes.new(type='ShaderNodeOutputMaterial')
        diffuse = nodes.new(type='ShaderNodeBsdfDiffuse')
        diffuse.inputs['Color'].default_value = material_config["color"]
        diffuse.inputs['Roughness'].default_value = material_config["roughness"]
        links.new(diffuse.outputs['BSDF'], output.inputs['Surface'])
        obj.data.materials.append(mat)
    else:
        for mat_slot in obj.material_slots:
            if mat_slot.material and mat_slot.material.use_nodes:
                bsdf = mat_slot.material.node_tree.nodes.get("Principled BSDF")
                if bsdf:
                    bsdf.inputs["Base Color"].default_value = material_config["color"]
                    bsdf.inputs["Roughness"].default_value = material_config["roughness"]
    logger.debug(f"Applied material to {obj.name}.")

def create_camera() -> bpy.types.Object:
    """Create orthographic camera."""
    cam_data = bpy.data.cameras.new(name="render_camera")
    cam_data.type = 'ORTHO'
    cam = bpy.data.objects.new(name="render_camera", object_data=cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    bpy.context.view_layer.update()
    logger.debug("Camera created.")
    return cam

def position_camera(cam: bpy.types.Object, view_name: str, dimensions: Dict[str, float], camera_config: Dict) -> None:
    """Position camera for specified view."""
    loc, rot = camera_config[view_name]
    cam.location = loc
    cam.rotation_euler = rot
    cam.data.ortho_scale = (
        max(dimensions["width"], dimensions["height"]) if view_name in ["front", "back"] else
        max(dimensions["depth"], dimensions["height"]) if view_name in ["left", "right"] else
        max(dimensions["width"], dimensions["depth"])
    )
    logger.debug(f"Camera positioned for {view_name}.")

def enable_freestyle() -> None:
    """Enable Freestyle rendering."""
    bpy.context.scene.render.use_freestyle = True
    bpy.context.scene.view_layers[0].use_freestyle = True
    logger.debug("Freestyle rendering enabled.")

def set_render_settings(scene: bpy.types.Scene, view_name: str, width_mm: float, height_mm: float, dpi: int, output_dir: Path) -> None:
    """Configure render settings for a view."""
    scene.render.resolution_x = int(width_mm * dpi / 25.4)
    scene.render.resolution_y = int(height_mm * dpi / 25.4)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(output_dir / f"{view_name}.png")
    logger.debug(f"Render settings for {view_name}: {scene.render.resolution_x}x{scene.render.resolution_y}")

def render_view(view_name: str, cam: bpy.types.Object, dimensions: Dict[str, float], config: Dict) -> None:
    """Render a specific view."""
    width_mm = dimensions[config["views"][view_name]["width"]]
    height_mm = dimensions[config["views"][view_name]["height"]]
    position_camera(cam, view_name, dimensions, config["camera_views"])
    set_render_settings(bpy.context.scene, view_name, width_mm, height_mm, config["dpi"], config["output_dir"])
    bpy.ops.render.render(write_still=True)
    logger.info(f"Rendered {view_name} view.")

def render_model(
    model_path: Path,
    block_width: Optional[float] = None,
    block_height: Optional[float] = None,
    block_depth: Optional[float] = None,
    config: Dict = CONFIG
) -> None:
    """Render orthographic views of a 3D model scaled to fit specified block dimensions."""
    try:
        check_blender_version()
        ensure_output_directory(config["output_dir"])
        clean_scene()
        obj = import_model(model_path)

        target_dims = {
            key: value for key, value in
            [("width", block_width), ("height", block_height), ("depth", block_depth)]
            if value is not None
        }
        final_target_dims, _ = center_and_align(obj, target_dims)
        add_block_frame(final_target_dims)
        setup_lighting(config)
        apply_material(obj, config["material"])
        enable_freestyle()

        scene = bpy.context.scene
        scene.render.film_transparent = True
        scene.render.image_settings.color_mode = 'RGBA'

        cam = create_camera()
        for view_name in config["views"]:
            render_view(view_name, cam, final_target_dims, config)
        
        logger.info(f"Rendering complete. Output saved to {config['output_dir']}")
    except Exception as e:
        logger.error(f"Rendering failed: {e}")
        raise

def main() -> None:
    """Entry point for command-line execution."""
    try:
        model_path, block_width, block_height, block_depth = parse_arguments()
        render_model(model_path, block_width, block_height, block_depth)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()