# ComfyDL

**ComfyDL** is a robust Command Line Interface (CLI) tool for downloading models for ComfyUI. It automates the process of fetching models from various sources (like Hugging Face, Civitai) and placing them into the correct directories within your ComfyUI installation.

## Install ComfyUI Models with Ease

```bash
comfydl flux
comfydl pony
comfydl sd15
comfydl qwen_image_edit
comfydl chilloutmix
comfydl civitai 354657 # Dreamshaper lightning DPM++ SDE
```

## Features

-   **Smart Downloads**: Automatically places files in the correct `models/*` subdirectories (e.g., `models/ipadapter`, `models/diffusion_models`).
-   **Multi-Source Support**: Easily download from Hugging Face, Civitai, and more using YAML configurations.
-   **Interactive Menu**: Select models to download from a user-friendly list.
-   **Resumable**: Uses `aria2c` (recommended) or `wget` for reliable, resumable downloads.
-   **Configurable**: Set your ComfyUI root path and API tokens once, and they are remembered.

## Requirements

-   **Python 3.8+**
-   **Download Tools**: `aria2c` (highly recommended for speed) or `wget`.
    -   macOS: `brew install aria2`
    -   Linux: `sudo apt install aria2`
    -   Windows: `choco install aria2`

## Installation

```bash
pip install git+https://github.com/ShinChven/comfydl.git
```

```bash
pip install -U git+https://github.com/ShinChven/comfydl.git
```

## Jupyter / Colab Setup

```python
!apt-get update && apt-get install aria2
!pip install git+https://github.com/ShinChven/comfydl.git
!comfydl set COMFYUI_ROOT /content/ComfyUI
!mkdir /content/ComfyUI/
```

## Configuration

Before starting, configure your ComfyUI root directory. You can also set a Civitai token if downloading restricted models.

```bash
# Set ComfyUI Root Path
comfydl set COMFYUI_ROOT /path/to/your/ComfyUI

# (Optional) Set Civitai API Token
comfydl set CIVITAI_TOKEN your_api_token

# (Optional) Set Hugging Face Token (for private/gated models)
comfydl set HF_TOKEN your_hf_token
```

*These settings are persisted locally in `~/.comfydl_config`.*

## Usage

### Interactive Mode

Simply run `comfydl` without arguments to launch the interactive menu. You can select multiple model sets to download.

```bash
comfydl
```

### Command Line Mode

Download a specific model set directly by name:

```bash
# General syntax
comfydl <model_source_name> [comfyui_path_override]

# Examples
comfydl flux
comfydl ipadapters
comfydl z_image
```

### Civitai Download

You can quickly download a model from Civitai using its Model Version ID or directly using the download URL. The tool will automatically determine the correct folder (e.g., `models/checkpoints`, `models/loras`) based on the model type.

```bash
# Using Model Version ID
comfydl civitai 1234567

# Using Direct Download URL
comfydl civitai "https://civitai.com/api/download/models/12345?type=Model&format=SafeTensor"

# Optional: Override ComfyUI root path
comfydl civitai 12345 /path/to/ComfyUI
```

*Note: If you have configured `CIVITAI_TOKEN`, it will be automatically appended to the request to support downloading restricted or early-access models.*

### Model Sources & Resolution

`comfydl` resolves model source names (e.g., `flux`) by checking locations in the following order:

1.  **Exact File Path**: If you provide a path to a YAML file, it is used directly.
2.  **User Global Storage**: Checks `~/.comfydl/model_sources/<name>.yaml`.
    *   Use this to override built-in sources or add personal collections available globally.
3.  **Built-in Sources**: Checks the `model_sources` directory bundled with the installed `comfydl` package.
4.  **Local Project Storage**: Checks `model_sources/<name>.yaml` in your current working directory.

### Custom Model Sources

To define your own model source, create a YAML file. You can place it in `~/.comfydl/model_sources/` to make it discoverable by name (e.g., `comfydl mysource`).

**YAML Format Example:**

```yaml
description: "My Custom Model Collection"
downloads:
  - url: "https://huggingface.co/some/model.safetensors"
    dest: "models/checkpoints/model.safetensors"
  - url: "https://civitai.com/api/download/models/12345"
    dest: "models/loras/mylora.safetensors"
```

## Contributing

### Adding New Default Sources

If you are a maintainer or contributor wishing to add new built-in model sources to the package, please refer to [MODEL_SOURCE.md](MODEL_SOURCE.md).

## Legacy Scripts

The original shell scripts (e.g., `download-ipadapters.sh`) are still present in the repository for reference but `comfydl` is the recommended way to download models.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
