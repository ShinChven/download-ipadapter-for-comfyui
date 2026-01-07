import argparse
import os
import sys
import yaml
from pathlib import Path
from .config import set_config_value, get_config_value
from .utils import check_downloader, download_file
import questionary

def handle_set(key, value):
    valid_keys = ["COMFYUI_ROOT", "CIVITAI_TOKEN"]
    if key not in valid_keys:
        print(f"Warning: '{key}' is not a standard configuration key. Valid keys: {valid_keys}")
    set_config_value(key, value)

def resolve_model_source(source_name):
    # Check if exact path
    if os.path.exists(source_name):
        return source_name

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
            
    # Check current working directory for local overrides/custom files
    cwd_sources = Path("model_sources")
    if cwd_sources.exists():
         candidate = cwd_sources / f"{source_name}.yaml"
         if candidate.exists():
             return str(candidate)
             
    # Maybe package provided sources? For now we assume local execution context
    return None

def get_available_sources():
    sources = set()
    
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
    
    # Check local
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
        
    downloads = config_data if isinstance(config_data, list) else config_data.get('downloads', [])
    
    for item in downloads:
        url = item.get('url')
        dest = item.get('dest')
        
        if not url or not dest:
            print(f"Skipping invalid item: {item}")
            continue
            
        full_dest = os.path.join(comfyui_path, dest)
        download_file(url, full_dest, downloader)
    return True

def main():
    parser = argparse.ArgumentParser(description="ComfyDL: ComfyUI Model Downloader")
    subparsers = parser.add_subparsers(dest="command")
    
    # Set command
    set_parser = subparsers.add_parser("set", help="Set configuration values")
    set_parser.add_argument("key", help="Configuration key (e.g., COMFYUI_ROOT, CIVITAI_TOKEN)")
    set_parser.add_argument("value", help="Configuration value")
    
    # args are tricky because we want positional args for download but 'set' is a command
    # simple approach: check sys.argv[1] manually or use simple argparse logic
    
    # The requirement: comfydl <model_source> [comfyui_path]
    # And: comfydl set <key> <value>
    
    if len(sys.argv) > 1 and sys.argv[1] == "set":
        # Handle set manually or let argparse handle it if structured well
        pass
    else:
        # It's a download command
        # We need to add arguments for the main parser or implicit "download" command
        pass

    # Let's restructure to be robust
    if len(sys.argv) > 1 and sys.argv[1] == "set":
         args = parser.parse_args()
         handle_set(args.key, args.value)
         return

    # If not set, treat as download arguments
    parser = argparse.ArgumentParser(description="ComfyDL: ComfyUI Model Downloader")
    parser.add_argument("model_source", nargs="?", help="Model source name (e.g. 'flux') or path to YAML config")
    parser.add_argument("comfyui_path", nargs="?", help="ComfyUI root directory override")
    
    # If the first arg is 'set', this parser would fail/confuse, but we handled 'set' above.
    # However, 'comfydl set ...' falling here means sys.argv needs care.
    # Actually, argparse subcommands is better but user wants `comfydl <source>` directly, not `comfydl download <source>`.
    
    # So we used the manual check for 'set'.
    
    args = parser.parse_args()
    
    # Logic for download

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
            print("Expected a file path or a name in 'model_sources/' directory (e.g. 'flux' for 'model_sources/flux.yaml').")
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
