#!/bin/bash

# This script downloads Qwen Image Edit models for ComfyUI.
#
# Usage:
#   bash download_qwen_image_edit_models.sh /path/to/ComfyUI
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
        "https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors;$COMFYUI_PATH/models/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors"
        "https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning/resolve/main/Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors;$COMFYUI_PATH/models/loras/Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors"
        "https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_edit_2511_bf16.safetensors;$COMFYUI_PATH/models/diffusion_models/qwen_image_edit_2511_bf16.safetensors"
        "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors;$COMFYUI_PATH/models/vae/qwen_image_vae.safetensors"
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

    echo -e "\nStarting downloads for ComfyUI at: $COMFYUI_PATH"
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
    
    echo -e "\nAll downloads complete!"
}

main "$@"
