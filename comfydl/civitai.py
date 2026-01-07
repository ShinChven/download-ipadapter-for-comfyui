import os
import requests
import sys
from .config import get_config_value
from .utils import download_file, check_downloader

def get_safe_headers():
    token = get_config_value("CIVITAI_TOKEN")
    headers = {
        "User-Agent": "ComfyDL/1.0",
        "Content-Type": "application/json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def fetch_model_version(version_id):
    url = f"https://civitai.com/api/v1/model-versions/{version_id}"
    headers = get_safe_headers()
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 403:
             print("Error: 403 Forbidden. Is your CIVITAI_TOKEN correct and does it have permission?")
             return None
        if response.status_code == 404:
             print(f"Error: Model version {version_id} not found.")
             return None
             
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching model info: {e}")
        return None

def determine_folder(model_type):
    # Map Civitai types to ComfyUI folders
    # Checkpoints, LORA, LoCon, TextualInversion, Hypernetwork, ControlNet, VAE, Upscaler, MotionModule
    
    mapping = {
        "Checkpoint": "models/checkpoints",
        "LORA": "models/loras",
        "LoCon": "models/loras",
        "TextualInversion": "models/embeddings",
        "Hypernetwork": "models/hypernetworks",
        "ControlNet": "models/controlnet",
        "VAE": "models/vae",
        "Upscaler": "models/upscale_models",
        "MotionModule": "models/animatediff_models",
        # Default fallback
    }
    
    return mapping.get(model_type, "models/checkpoints")

import re

def extract_version_id(input_str):
    # Try as integer first
    if str(input_str).isdigit():
        return str(input_str)
        
    # Try regex for URL
    # Pattern: models/(\d+)
    match = re.search(r'models/(\d+)', str(input_str))
    if match:
        return match.group(1)
        
    return None

def process_civitai_download(input_str, comfyui_root, downloader=None):
    version_id = extract_version_id(input_str)
    
    if not version_id:
        print(f"Error: Could not extract model version ID from '{input_str}'.")
        return False

    if not downloader:
        downloader = check_downloader()
        if not downloader:
             print("Error: No downloader found (aria2c/wget).")
             return False

    print(f"Fetching info for model version: {version_id}...")
    data = fetch_model_version(version_id)
    
    if not data:
        return False
        
    model_info = data.get("model", {})
    files = data.get("files", [])
    
    model_name = model_info.get("name", "Unknown Model")
    model_type = model_info.get("type", "Checkpoint")
    
    print(f"Found model: {model_name} ({model_type})")
    
    if not files:
        print("Error: No files found for this model version.")
        return False
    
    # Find primary file, or default to first
    target_file = None
    for f in files:
        if f.get("primary"):
            target_file = f
            break
            
    if not target_file:
        target_file = files[0]
        
    file_name = target_file.get("name")
    download_url = target_file.get("downloadUrl")
    
    if not file_name or not download_url:
        print("Error: Invalid file data from API.")
        return False
        
    # Determine folder
    subfolder = determine_folder(model_type)
    dest_path = os.path.join(comfyui_root, subfolder, file_name)
    
    print(f"Target: {subfolder}/{file_name}")
    
    download_file(download_url, dest_path, downloader)
    return True
