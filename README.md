# ComfyUI Model Downloaders

A collection of robust shell scripts to download various model sets for ComfyUI.

These scripts automate the process of downloading models and placing them in the correct directories within your ComfyUI installation.

## Available Scripts

### 1. IP-Adapter Models (`download-ipadapters.sh`)
Downloads official IP-Adapter models (Standard, FaceID, SDXL) along with necessary CLIP Vision encoders and LoRAs.

### 2. Qwen Image Models (`download_qwen_image_models.sh`)
Downloads Qwen Image models including text encoders, LoRAs, diffusion models, and VAE.

### 3. Z-Image Models (`download_z_image_models.sh`)
Downloads Z-Image models including text encoders, diffusion models, and VAE.

## Features

- **Correct Placement:** Automatically places files in the correct `models/*` subdirectories (e.g., `models/ipadapter`, `models/diffusion_models`, `models/text_encoders`).
- **Efficient:** Uses `aria2c` for multi-connection accelerated downloads if installed; otherwise defaults to `wget`.
- **Smart Resume:** Skips existing complete files and resumes partial downloads.
- **Flexible Paths:** Accepts absolute or relative paths to your ComfyUI directory.

## Requirements

- A `bash` shell (macOS, Linux, WSL).
- `wget` OR `aria2c` installed.

## Usage

Run the desired script with `bash` and provide the path to your ComfyUI root directory.

### Download IP-Adapter Models
```bash
bash download-ipadapters.sh /path/to/ComfyUI
```

### Download Qwen Image Models
```bash
bash download_qwen_image_models.sh /path/to/ComfyUI
```

### Download Z-Image Models
```bash
bash download_z_image_models.sh /path/to/ComfyUI
```

### Examples
```bash
# If ComfyUI is in your home directory
bash download_qwen_image_models.sh ~/ComfyUI

# If you are already inside your ComfyUI directory
bash download_z_image_models.sh .
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
