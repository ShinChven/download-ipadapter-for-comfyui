import argparse
import os
import sys
import yaml
import math
from pathlib import Path
from .config import set_config_value, get_config_value
from .utils import check_downloader, download_file
import questionary

def format_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def handle_set(key, value):
    valid_keys = ["COMFYUI_ROOT", "CIVITAI_TOKEN", "HF_TOKEN", "MODEL_SOURCES_PATH"]
    if key not in valid_keys:
        print(f"Warning: '{key}' is not a standard configuration key. Valid keys: {valid_keys}")
    set_config_value(key, value)

def resolve_model_source(source_name):
    # Check if exact path
    if os.path.exists(source_name):
        return source_name

    # Check custom model sources path
    custom_sources_path = get_config_value("MODEL_SOURCES_PATH")
    if custom_sources_path and os.path.exists(custom_sources_path):
        custom_sources = Path(custom_sources_path)
        candidate = custom_sources / f"{source_name}.yaml"
        if candidate.exists():
            return str(candidate)

        candidate = custom_sources / source_name
        if candidate.exists():
            return str(candidate)

    # Check user home override directory (~/.comfydl/model_sources)
    user_sources = Path.home() / ".comfydl" / "model_sources"
    if user_sources.exists():
        candidate = user_sources / f"{source_name}.yaml"
        if candidate.exists():
            return str(candidate)

        candidate = user_sources / source_name
        if candidate.exists():
            return str(candidate)
    
    # Check in local model_sources directory (bundled with package)
    package_dir = Path(__file__).parent
    bundled_sources = package_dir / "model_sources"
    
    if bundled_sources.exists():
        candidate = bundled_sources / f"{source_name}.yaml"
        if candidate.exists():
            return str(candidate)
            
        candidate = bundled_sources / source_name
        if candidate.exists():
            return str(candidate)
            
    # Check in subdirectory of current working directory (comfydl/model_sources)
    local_dev_sources = Path("comfydl/model_sources")
    if local_dev_sources.exists():
        candidate = local_dev_sources / f"{source_name}.yaml"
        if candidate.exists():
            return str(candidate)
        
        candidate = local_dev_sources / source_name
        if candidate.exists():
            return str(candidate)
    cwd_sources = Path("model_sources")
    if cwd_sources.exists():
         candidate = cwd_sources / f"{source_name}.yaml"
         if candidate.exists():
             return str(candidate)
             
    # Maybe package provided sources? For now we assume local execution context
    return None

def get_available_sources():
    sources = set()
    
    # Check custom model sources path
    custom_sources_path = get_config_value("MODEL_SOURCES_PATH")
    if custom_sources_path and os.path.exists(custom_sources_path):
        for f in Path(custom_sources_path).glob("*.yaml"):
            sources.add(f.stem)

    # Check user home sources
    user_sources = Path.home() / ".comfydl" / "model_sources"
    if user_sources.exists():
        for f in user_sources.glob("*.yaml"):
            sources.add(f.stem)

    # Check bundled
    package_dir = Path(__file__).parent
    bundled_sources = package_dir / "model_sources"
    if bundled_sources.exists():
        for f in bundled_sources.glob("*.yaml"):
            sources.add(f.stem)
    
    # Check local development
    local_dev_sources = Path("comfydl/model_sources")
    if local_dev_sources.exists():
        for f in local_dev_sources.glob("*.yaml"):
            sources.add(f.stem)

    # Check local 'model_sources' directory
    cwd_sources = Path("model_sources")
    if cwd_sources.exists():
        for f in cwd_sources.glob("*.yaml"):
            sources.add(f.stem)
            
    return sorted(list(sources))

def process_download(model_source_path, comfyui_path, downloader=None):
    if not downloader:
        downloader = check_downloader()
        if not downloader:
            print("Error: Neither aria2c nor wget found. Please install one of them.")
            return False
            
    print(f"Using ComfyUI path: {comfyui_path}")
    print(f"\nProcessing: {os.path.basename(model_source_path)}")
    
    try:
        with open(model_source_path, 'r') as f:
            config_data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading YAML: {e}")
        return False
        
    if config_data is None:
        print(f"Error: Empty configuration file: {model_source_path}")
        return False

    downloads = []
    if isinstance(config_data, list):
        downloads = config_data
    elif isinstance(config_data, dict):
        downloads = config_data.get('downloads', [])
    
    if not downloads:
        print(f"Warning: No downloads found in {model_source_path}")
        return True

    for item in downloads:
        url = item.get('url')
        dest = item.get('dest')
        
        if not url or not dest:
            print(f"Skipping invalid item: {item}")
            continue
            
        full_dest = os.path.join(comfyui_path, dest)
        download_file(url, full_dest, downloader)
    return True

from .civitai import process_civitai_download

def main():
    parser = argparse.ArgumentParser(description="ComfyDL: ComfyUI Model Downloader")
    subparsers = parser.add_subparsers(dest="command")
    
    # Set command
    set_parser = subparsers.add_parser("set", help="Set configuration values")
    set_parser.add_argument("key", help="Configuration key (e.g., COMFYUI_ROOT, CIVITAI_TOKEN)")
    set_parser.add_argument("value", help="Configuration value")
    
    # Civitai command
    civitai_parser = subparsers.add_parser("civitai", help="Download model from Civitai by Model Version ID or URL")
    civitai_parser.add_argument("version_id", help="Civitai Model Version ID (integer) or Download URL")
    civitai_parser.add_argument("comfyui_path", nargs="?", help="ComfyUI root directory override")

    # Sources command
    subparsers.add_parser("sources", help="List available model sources")

    # List command (local models)
    list_parser = subparsers.add_parser("list", help="List downloaded models in ComfyUI models directory")
    list_parser.add_argument("comfyui_path", nargs="?", help="ComfyUI root directory override")

    # To handle the existing "default" behavior (comfydl <source>), we check sys.argv
    # If the first argument is a known command, we parse.
    # Otherwise, we treat it as the legacy/default behavior.
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "set":
            args = parser.parse_args()
            handle_set(args.key, args.value)
            return
        elif sys.argv[1] == "civitai":
            args = parser.parse_args()
            
            comfyui_path = args.comfyui_path
            if not comfyui_path:
                comfyui_path = get_config_value("COMFYUI_ROOT")
                
            if not comfyui_path:
                 # Fallback to current dir if it looks like ComfyUI? Or error
                 # Actually, let's enforce it or check current dir
                 pass # check below
                 
            if not comfyui_path:
                print("Error: ComfyUI path not specified.")
                sys.exit(1)
            
            # Check for main.py to confirm it's likely ComfyUI
            if not os.path.exists(os.path.join(comfyui_path, "main.py")):
                print(f"Warning: '{comfyui_path}' does not look like a ComfyUI directory (main.py missing).")

            process_civitai_download(args.version_id, comfyui_path)
            return
        elif sys.argv[1] == "sources":
            sources = get_available_sources()
            if not sources:
                print("No model sources found.")
            else:
                print("Available model sources:")
                for s in sources:
                    print(f"  - {s}")
            return
        elif sys.argv[1] == "list":
            args, _ = parser.parse_known_args()
            comfyui_path = args.comfyui_path
            if not comfyui_path:
                comfyui_path = get_config_value("COMFYUI_ROOT")
            
            if not comfyui_path:
                print("Error: ComfyUI path not specified.")
                sys.exit(1)
            
            comfyui_path = os.path.abspath(comfyui_path)
            models_dir = os.path.join(comfyui_path, "models")
            
            if not os.path.exists(models_dir):
                print(f"Error: Models directory not found at {models_dir}")
                sys.exit(1)
            
            print(f"Models in {models_dir}:")
            found = False
            total_size = 0
            for root, dirs, files in os.walk(models_dir):
                for file in files:
                    if file.startswith('.') or file.endswith('.txt') or file.endswith('.md'):
                        continue
                    found = True
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, models_dir)
                    size = os.path.getsize(file_path)
                    total_size += size
                    size_str = format_size(size)
                    print(f"  - [{size_str:>10}] {rel_path}")
            
            if not found:
                print("  (No models found)")
            else:
                print(f"\nTotal size: {format_size(total_size)}")
            return

    # If not a subcommand, use the original parser logic for sources
    parser = argparse.ArgumentParser(description="ComfyDL: ComfyUI Model Downloader")
    parser.add_argument("model_source", nargs="?", help="Model source name (e.g. 'flux') or path to YAML config")
    parser.add_argument("comfyui_path", nargs="?", help="ComfyUI root directory override")
    
    args = parser.parse_args()
    
    # Logic for download
    # Check for ComfyUI path first as it is required for any download
    comfyui_path = args.comfyui_path
    if not comfyui_path:
        comfyui_path = get_config_value("COMFYUI_ROOT")
        
    if not comfyui_path:
        print("Error: ComfyUI path not specified.")
        print("Provide it as an argument: comfydl <source> <path>")
        print("Or set it globally: comfydl set COMFYUI_ROOT <path>")
        sys.exit(1)
        
    comfyui_path = os.path.abspath(comfyui_path)
    if not os.path.exists(comfyui_path):
        print(f"Error: ComfyUI directory '{comfyui_path}' does not exist.")
        sys.exit(1)

    # Check for main.py to confirm it's likely ComfyUI
    if not os.path.exists(os.path.join(comfyui_path, "main.py")):
        print(f"Warning: '{comfyui_path}' does not look like a ComfyUI directory (main.py missing).")

    downloader = check_downloader()
    if not downloader:
        print("Error: Neither aria2c nor wget found. Please install one of them.")
        sys.exit(1)
    print(f"Using downloader: {downloader}")

    if args.model_source:
        model_source_path = resolve_model_source(args.model_source)
        if not model_source_path:
            print(f"Error: Model source '{args.model_source}' not found.")
            print("Try 'comfydl sources' to see available sources.")
            sys.exit(1)
        
        process_download(model_source_path, comfyui_path, downloader)
    else:
        # Interactive mode
        sources = get_available_sources()
        if not sources:
            print("No model sources found in 'model_sources' directory.")
            sys.exit(1)
            
        selected = questionary.checkbox(
            "Select model sources to download:",
            choices=sources
        ).ask()
        
        if not selected:
            print("No sources selected.")
            sys.exit(0)
            
        for source_name in selected:
             model_source_path = resolve_model_source(source_name)
             if model_source_path:
                 process_download(model_source_path, comfyui_path, downloader)

if __name__ == "__main__":
    main()
