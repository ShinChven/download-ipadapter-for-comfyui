# ComfyDL

**ComfyDL** is a robust Command Line Interface (CLI) tool for downloading models for ComfyUI. It automates the process of fetching models from various sources (like Hugging Face, Civitai) and placing them into the correct directories within your ComfyUI installation.

It replaces the legacy collection of shell scripts with a unified, configurable Python application.

## Features

-   **Smart Downloads**: Automatically places files in the correct `models/*` subdirectories (e.g., `models/ipadapter`, `models/diffusion_models`).
-   **Multi-Source Support**: Easily download from Hugging Face, Civitai, and more using YAML configurations.
-   **Interactive Menu**: Select models to download from a user-friendly list.
-   **Resumable**: Uses `aria2c` (recommended) or `wget` for reliable, resumable downloads.
-   **Configurable**: Set your ComfyUI root path and API tokens once, and they are remembered.

## Installation

You can install `comfydl` directly from the source:

```bash
git clone https://github.com/ShinChven/download-ipadapter-for-comfyui.git
cd download-ipadapter-for-comfyui
pip install -e .
```

*Using a virtual environment is recommended.*

## Requirements

-   **Python 3.8+**
-   **Download Tools**: `aria2c` (highly recommended for speed) or `wget`.
    -   macOS: `brew install aria2`
    -   Linux: `sudo apt install aria2`

## Configuration

Before starting, configure your ComfyUI root directory. You can also set a Civitai token if downloading restricted models.

```bash
# Set ComfyUI Root Path
comfydl set COMFYUI_ROOT /path/to/your/ComfyUI

# (Optional) Set Civitai API Token
comfydl set CIVITAI_TOKEN your_api_token
```

*These settings are persisted locally.*

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

### Custom Model Sources

`comfydl` comes with built-in configurations (e.g., `flux`, `ipadapters`). You can verify available sources by looking at the `comfydl/model_sources` directory.

To use your own custom model list, create a YAML file and pass its path:

```bash
comfydl my_custom_models.yaml
```

**YAML Format Example:**

```yaml
downloads:
  - url: "https://huggingface.co/some/model.safetensors"
    dest: "models/checkpoints/model.safetensors"
  - url: "https://civitai.com/api/download/models/12345"
    dest: "models/loras/mylora.safetensors"
```

## Legacy Scripts

The original shell scripts (e.g., `download-ipadapters.sh`) are still present in the repository for reference but `comfydl` is the recommended way to download models.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
