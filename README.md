# 3D Model Reference Renderer for Woodcarving

## Overview

This project provides a Blender-based Python script (`script.py`) designed for woodcarvers to generate high-quality, orthographic reference images from 3D models. The script scales a 3D model to fit a specified wooden block size and renders five views (front, back, left, right, top) as PNG images. These images can be printed and glued onto a wooden block to guide carving, ensuring accurate proportions and alignment with the block’s dimensions.

The script supports flexible block sizing: you can specify 1, 2, or 3 dimensions (width, height, depth in mm), and it calculates missing dimensions to maintain the model’s proportions. It includes features like Freestyle edge rendering, high-contrast materials, and a wireframe bounding box for visualization.

## Features

- **Imports GLTF Models**: Supports `.glb` and `.gltf` file formats.
- **Flexible Scaling**: Scales the model to fit specified block dimensions (1–3 dimensions provided).
- **Orthographic Views**: Renders front, back, left, right, and top views as PNG images.
- **High-Contrast Rendering**: Applies a uniform material for clear reference images.
- **Wireframe Bounding Box**: Visualizes the block size in Blender for verification.
- **Customizable Configuration**: Adjust DPI, lighting, and camera settings via a configuration dictionary.

## Requirements

To use this script, you need the following software:

- **Blender**: Version 4.0.0 or higher
  - Download from [blender.org](https://www.blender.org/download/)
- **Python**: Version 3.10 or higher (included with Blender)
  - No additional Python installation is typically required, as Blender includes its own Python interpreter.
- **Operating System**: Windows, macOS, or Linux (Blender-compatible)

No additional Python packages are required, as the script uses Blender’s built-in Python environment and standard libraries.

## Installation

1. **Install Blender**:
   - Download and install Blender (version 4.0.0 or higher) from [blender.org](https://www.blender.org/download/).
   - Ensure Blender is added to your system’s PATH for command-line execution.

2. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/3d-model-reference-renderer.git
   cd 3d-model-reference-renderer
   ```

3. **Prepare Your 3D Model**:
   - Ensure your 3D model is in `.glb` or `.gltf` format.
   - Place the model file in the project directory or specify its path when running the script.

## Usage

The script can be run via the command line using Blender’s background mode (`-b`) or imported as a Python module for custom workflows.

### Command-Line Usage

Run the script with Blender in background mode to generate reference images. The general syntax is:

```bash
blender -b -P script.py -- --model <path_to_model> [--block-width <width>] [--block-height <height>] [--block-depth <depth>]
```

#### Arguments
- `--model <path>`: Path to the `.glb` or `.gltf` model file (default: `model.glb`).
- `--block-width <float>`: Width of the wooden block in mm (X-axis).
- `--block-height <float>`: Height of the wooden block in mm (Z-axis).
- `--block-depth <float>`: Depth of the wooden block in mm (Y-axis).

At least one dimension (`--block-width`, `--block-height`, or `--block-depth`) must be provided. Missing dimensions are calculated to maintain the model’s proportions.

#### Examples

1. **Render with a single dimension (width = 100 mm)**:
   ```bash
   blender -b -P script.py -- --model model.glb --block-width 100
   ```
   - Scales the model so its width is 100 mm, with depth and height proportional.
   - Outputs images to the `output` directory (e.g., `output/front.png`, `output/back.png`, etc.).

2. **Render with two dimensions (width = 100 mm, height = 50 mm)**:
   ```bash
   blender -b -P script.py -- --model model.glb --block-width 100 --block-height 50
   ```
   - Scales the model to fit a 100 mm width and 50 mm height, calculating depth proportionally.

3. **Render with all dimensions (width = 100 mm, height = 50 mm, depth = 75 mm)**:
   ```bash
   blender -b -P script.py -- --model model.glb --block-width 100 --block-height 50 --block-depth 75
   ```
   - Scales the model to fit exactly within the specified block.

4. **Use a custom model path**:
   ```bash
   blender -b -P script.py -- --model /path/to/custom_model.glb --block-width 120
   ```

#### Output
- Images are saved in the `output` directory (created automatically).
- Each view (`front`, `back`, `left`, `right`, `top`) is saved as a PNG file with transparent background and Freestyle edges for clarity.
- Resolution is based on the block dimensions and DPI (default: 300 DPI).

### Library Usage

You can import the script as a Python module in another Blender script for custom workflows:

```python
from render_model import render_model

# Render with custom configuration
config = {
    "output_dir": Path("custom_output").absolute(),
    "dpi": 600,
    # ... other config options
}
render_model(
    model_path=Path("model.glb"),
    block_width=100,
    block_height=50,
    config=config
)
```

### Notes
- Ensure dimensions are positive numbers (e.g., `100`, not `-100` or `0`).
- The model must have non-zero dimensions in all axes (width, height, depth).
- Output images are sized in pixels based on the formula: `pixels = mm * DPI / 25.4`.

## Project Structure

```
3d-model-reference-renderer/
├── script.py       # Main script
├── README.md       # This file
├── output/         # Output directory for rendered images
└── model.glb       # Example model (not included)
```

## Troubleshooting

- **Error: "Blender version unsupported"**
  - Ensure Blender 4.0.0 or higher is installed.
- **Error: "Model file does not exist"**
  - Verify the model path and file extension (`.glb` or `.gltf`).
- **Error: "Block <dimension> must be positive"**
  - Provide positive values for `--block-width`, `--block-height`, or `--block-depth`.
- **No mesh object found**
  - Ensure the GLTF model contains at least one mesh object.

For additional help, check the logs printed to the console or file an issue on GitHub.

## License

This project is licensed under the MIT License. See `LICENSE` for details.