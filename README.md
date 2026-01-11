# ComfyDL

[![PyPI version](https://img.shields.io/pypi/v/comfydl.svg)](https://pypi.org/project/comfydl/)
[![Python versions](https://img.shields.io/pypi/pyversions/comfydl.svg)](https://pypi.org/project/comfydl/)
[![License](https://img.shields.io/pypi/l/comfydl.svg)](https://github.com/ShinChven/comfydl/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/comfydl.svg)](https://pypi.org/project/comfydl/)

**ComfyDL** is a robust Command Line Interface (CLI) tool for downloading models for ComfyUI. It automates the process of fetching models from various sources (like Hugging Face, Civitai) and placing them into the correct directories within your ComfyUI installation.

## Install ComfyUI Models with Ease

```sh
comfydl flux1
comfydl flux1_dev_fp8
comfydl pony
comfydl dreamshaper
comfydl common_vae
comfydl qwen_image_edit
comfydl chilloutmix
comfydl civitai 354657 # By Version ID
comfydl "urn:air:flux1:checkpoint:civitai:618692@691639" # By AIR URN
```

## Features

-   **Smart Downloads**: Automatically places files in the correct `models/*` subdirectories (e.g., `models/ipadapter`, `models/diffusion_models`).
-   **Installation Status & Audit**: Use `sources --installed` to see exactly what's installed, including file sizes and partial installation status.
-   **Smart Removal**: Safely uninstall models by source name using the `rm` command, including dry-run and interative modes.
-   **Civitai Integration**: Quick download via Model ID, Version ID, URLs, or **AIR URNs** (`urn:air:...@version`).
-   **Model Registries**: Subscribe to remote JSON registries for dynamic model source updates.
-   **Safety Confirmations**: Prompts for confirmation before significant actions (downloads, deletions) and warns about low disk space.
-   **Resumable**: Uses `aria2c` (recommended) or `wget` for reliable, resumable downloads.
-   **Configurable**: Set your ComfyUI root path and API tokens once, and they are remembered.

## Requirements

-   **Python 3.8+**
-   **Download Tools**: `aria2c` (highly recommended for speed) or `wget`.
    -   macOS: `brew install aria2`
    -   Linux: `sudo apt install aria2`
    -   Windows: `choco install aria2`

## Installation

### Via PyPI (Recommended)

```bash
pip install comfydl
```

### Via Git

```bash
pip install git+https://github.com/ShinChven/comfydl.git
```

To update:
```bash
pip install -U git+https://github.com/ShinChven/comfydl.git
```

## Jupyter / Colab Setup

```python
!apt-get update && apt-get install aria2
!pip install comfydl
!comfydl set COMFYUI_ROOT /content/ComfyUI
!mkdir -p /content/ComfyUI/
```

## Configuration

Before starting, configure your ComfyUI root directory and any necessary API tokens. These settings are persisted locally in `~/.comfydl_config`.

| Key | Description | Command Example |
| :--- | :--- | :--- |
| `COMFYUI_ROOT` | **Required**. Path to your ComfyUI root directory. | `comfydl set COMFYUI_ROOT /path/to/ComfyUI` |
| `CIVITAI_TOKEN` | (Optional) Token for restricted or early access Civitai models. | `comfydl set CIVITAI_TOKEN your_token` |
| `HF_TOKEN` | (Optional) Token for private or gated Hugging Face models. | `comfydl set HF_TOKEN your_token` |
| `MODEL_SOURCES_PATH`| (Optional) Custom directory to search for YAML model sources. | `comfydl set MODEL_SOURCES_PATH /custom/sources` |

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
comfydl <model_source_name> -y  # Skip confirmation

# Examples
comfydl flux
comfydl ipadapters
comfydl z_image
```

### Direct Resource Download

Download any model directly using a Standard URL or an **AI Resource Identifier (AIR)**. `comfydl` will help you organize it.

```bash
# Download from a Standard URL (interactive folder selection)
comfydl https://example.com/model.safetensors

# Download using AI Resource Identifier (AIR) (automatically switches to Civitai mode)
comfydl "urn:air:flux1:checkpoint:civitai:618692@691639"

# Download matching a known source (auto-selects destination)
comfydl https://huggingface.co/comfyanonymous/ControlNet-v1-1_fp16_safetensors/resolve/main/control_v11p_sd15_inpaint_fp16.safetensors

# Download and specify the destination folder (non-interactive)
comfydl https://example.com/model.safetensors -d models/checkpoints

# Skip confirmation prompts
comfydl https://example.com/model.safetensors -y
```

**Features:**
*   **Intelligent Suggestion**: It searches your known model sources to automatically suggest the correct folder (e.g. if the URL matches a known ControlNet model, it suggests `models/controlnet`).
*   **Disk Space Check**: Automatically checks if you have enough free space before downloading.

### Listing & Checking Models

List all available model sources or check their installation status with file sizes.

```bash
# List all available names
comfydl sources

# Check installation status with a detailed tree view and file sizes
comfydl sources --installed

# List all large files in your ComfyUI models directory
comfydl list
```

**Status Indicators:**
- `[✓]` Entire source/component is installed.
- `[ ]` Source/component is missing.
- `[!]` Source is partially installed (some components are missing).

### Removing Models

Safely remove files associated with one or more model sources.

```bash
# Uninstall a specific source
comfydl rm flux1

# Interactive removal menu
comfydl rm

# Dry run (see what would be deleted)
comfydl rm flux1 --dry-run

# Force removal without confirmation
comfydl rm flux1 -f
```

### Civitai Download

You can quickly download a model from Civitai using its Model Version ID, **AI Resource Identifier (AIR)**, or directly using the download URL. The tool will automatically determine the correct folder (e.g., `models/checkpoints`, `models/loras`) based on the model type.

```bash
# Using Model Version ID
comfydl civitai 1234567

# Using AI Resource Identifier (AIR) (must contain @version_id)
comfydl civitai "urn:air:flux1:checkpoint:civitai:618692@691639"

# Using Direct Download URL or Model URL with modelVersionId
comfydl civitai "https://civitai.com/models/618692?modelVersionId=691639"
comfydl civitai "https://civitai.com/api/download/models/691639?type=Model&format=SafeTensor&size=pruned&fp=fp32"

# Optional: Override ComfyUI root path
comfydl civitai 12345 /path/to/ComfyUI
```

*Note: If you have configured `CIVITAI_TOKEN`, it will be automatically appended to the request to support downloading restricted or early-access models.*

### Model Registries

ComfyDL supports subscribing to remote registries (JSON files) to keep your model sources dynamic and up-to-date. The default registry is automatically configured.

```bash
# List configured registries
comfydl registry list

# Add a new registry
comfydl registry add https://example.com/my-sources.json --name specific_repo

# Update local cache of registries (fetches latest changes)
comfydl registry update

# Remove a registry
comfydl registry delete https://example.com/my-sources.json
```

Registries are cached locally in `~/.comfydl/registries/`.

### Model Sources & Resolution

`comfydl` resolves model source names (e.g., `flux`) by checking locations in the following order:

1.  **Exact File Path**: If you provide a path to a YAML file, it is used directly.
2.  **Custom Model Sources Path**: Checks the directory configured via `comfydl set MODEL_SOURCES_PATH <path>`.
3.  **Registries**: Checks cached sources from subscribed registries (including default).
4.  **Built-in Sources**: Checks the bundled `model_sources` directory (legacy).

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
