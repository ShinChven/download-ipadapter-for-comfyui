#!/bin/bash

# This script downloads Z-Image models for ComfyUI.
#
# Usage:
#   bash download_z_image_models.sh /path/to/ComfyUI
#
# It will download any missing model files to the correct directories.

set -e

# --- Helper Functions ---

command_exists() {
    command -v "$1" &> /dev/null
}

set_downloader() {
    if command_exists aria2c; then
        DOWNLOADER="aria2c -x 16 -s 16 -k 1M --console-log-level=warn -c"
        echo "Using aria2c for downloads."
    elif command_exists wget; then
        DOWNLOADER="wget -c"
        echo "Using wget for downloads."
    else
        echo "Error: Neither aria2c nor wget found. Please install one of them."
        exit 1
    fi
}

# Note: This function uses the '-c' flag for wget/aria2c. This means it will
# automatically skip downloading a file if it already exists and is complete.
# It will resume partial downloads if any. It will NOT delete or overwrite
# existing complete files.
download_file() {
    local url="$1"
    local filepath="$2"
    local filename=$(basename "$filepath")
    local dir=$(dirname "$filepath")

    echo "Downloading $filename..."
    mkdir -p "$dir"

    if [[ $DOWNLOADER == "aria2c"* ]]; then
        $DOWNLOADER -d "$dir" -o "$filename" "$url"
    else
        $DOWNLOADER -O "$filepath" "$url"
    fi

    if [ $? -eq 0 ]; then
        echo "$filename downloaded successfully."
    else
        echo "Error downloading $filename."
    fi
}

# --- Download Definitions ---

define_downloads() {
    local COMFYUI_PATH="$1"
    # Global array
    DOWNLOADS_DEF=(
        "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors;$COMFYUI_PATH/models/text_encoders/qwen_3_4b.safetensors"
        "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo_bf16.safetensors;$COMFYUI_PATH/models/diffusion_models/z_image_turbo_bf16.safetensors"
        "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors;$COMFYUI_PATH/models/vae/ae.safetensors"
        "https://huggingface.co/alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union/resolve/main/Z-Image-Turbo-Fun-Controlnet-Union.safetensors;$COMFYUI_PATH/models/model_patches/Z-Image-Turbo-Fun-Controlnet-Union.safetensors"
    )
}

# --- Main ---

main() {
    if [ -z "$1" ]; then
        echo "Usage: $0 /path/to/ComfyUI"
        exit 1
    fi

    if [ ! -d "$1" ]; then
        echo "Error: Directory '$1' not found."
        exit 1
    fi

    local COMFYUI_PATH=$(cd "$1" && pwd)
    
    if [ ! -f "$COMFYUI_PATH/main.py" ]; then
        echo "Warning: '$COMFYUI_PATH' does not look like a ComfyUI directory."
        read -p "Continue anyway? (y/n) " -n 1 -r; echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 1; fi
    fi

    set_downloader
    define_downloads "$COMFYUI_PATH"

    echo -e "
Starting downloads for ComfyUI at: $COMFYUI_PATH"
    echo "Checking for missing files..."

    for item in "${DOWNLOADS_DEF[@]}"; do
        IFS=';' read -r url dest_path <<< "$item"
        # The -c flag in the downloader will handle skipping completed files,
        # but we add a check here to be more explicit and avoid downloader output.
        if [ -f "$dest_path" ]; then
            echo "Skipping existing file: $(basename "$dest_path")"
        else
            download_file "$url" "$dest_path"
        fi
    done
    
    echo -e "
All downloads complete!"
}

main "$@"
