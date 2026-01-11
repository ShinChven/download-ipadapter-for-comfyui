import argparse
import os
import sys
import yaml
import math
from pathlib import Path
from .config import set_config_value, get_config_value
from .utils import check_downloader, download_file, get_remote_file_size, format_size, check_disk_space
import questionary
from . import __version__
from .registry import init_registries, update_registry, load_registry_sources, resolve_registry_source, add_registry, remove_registry, get_registries




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

def get_source_config(source_name):
    """
    Resolve a source name to a configuration dictionary.
    Returns (config_dict, source_origin_description)
    """
    # 1. Check local file paths (legacy/development override)
    path = resolve_model_source(source_name)
    if path:
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f), path
        except Exception as e:
            print(f"Error loading local source {path}: {e}")
            return None, None

    # 2. Check registries
    init_registries()
    config = resolve_registry_source(source_name)
    if config:
        return config, f"registry:{source_name}"
        
    return None, None

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
            
    # Add registry sources
    init_registries()
    registry_sources = load_registry_sources()
    sources.update(registry_sources.keys())

    return sorted(list(sources))

def get_downloads_status(downloads, comfyui_path, fetch_remote_size=False):
    """
    Check the status of download items.
    Returns a list of (dest, is_installed, local_size, remote_size).
    """
    items_status = []
    for item in downloads:
        url = item.get('url')
        dest = item.get('dest')
        if not dest:
            continue
        
        full_path = os.path.join(comfyui_path, dest)
        is_installed = os.path.exists(full_path) and os.path.isfile(full_path)
        
        local_size = os.path.getsize(full_path) if is_installed else 0
        remote_size = None
        
        if not is_installed and fetch_remote_size and url:
            remote_size = get_remote_file_size(url)
            
        items_status.append({
            'dest': dest,
            'is_installed': is_installed,
            'local_size': local_size,
            'remote_size': remote_size,
            'url': url
        })
    return items_status

def print_source_tree(source_name, items_status, indent=""):
    """
    Print a formatted file tree for a model source.
    """
    installed_count = sum(1 for item in items_status if item['is_installed'])
    total_count = len(items_status)
    total_local_size = sum(item['local_size'] for item in items_status)
    
    # Calculate padding for alignment
    max_label_len = 0
    if total_count == 1:
        max_label_len = len(source_name)
    else:
        max_label_len = len(source_name)
        for item in items_status:
            name = os.path.basename(item['dest'])
            # 4 spaces for "  └── " or "  ├── "
            max_label_len = max(max_label_len, len(name) + 4)
    
    # Cap padding to avoid excessive width on very long filenames
    padding = min(max_label_len, 60)
    
    if total_count == 1:
        item = items_status[0]
        status_symbol = "✓" if item['is_installed'] else " "
        size_str = ""
        if item['is_installed']:
            size_str = f" [{format_size(item['local_size']):>10}]"
        elif item['remote_size']:
            size_str = f" [{format_size(item['remote_size']):>10}] (remote)"
            
        label = f"[{status_symbol}] {source_name}"
        print(f"{indent}{label:<{padding + 4}}{size_str}")
    else:
        status_symbol = "✓" if installed_count == total_count else ("!" if installed_count > 0 else " ")
        total_size_str = f" [{format_size(total_local_size):>10}]" if total_local_size > 0 else ""
        
        label = f"[{status_symbol}] {source_name}"
        print(f"{indent}{label:<{padding + 4}} ({installed_count}/{total_count}){total_size_str}")
        
        for i, item in enumerate(items_status):
            connector = "└──" if i == len(items_status) - 1 else "├──"
            item_symbol = "✓" if item['is_installed'] else " "
            
            size_str = ""
            if item['is_installed']:
                size_str = f" [{format_size(item['local_size']):>10}]"
            elif item['remote_size']:
                size_str = f" [{format_size(item['remote_size']):>10}] (remote)"
            
            name = os.path.basename(item['dest'])
            child_label = f" {connector} [{item_symbol}] {name}"
            print(f"{indent}  {child_label:<{padding + 2}}{size_str}")

def process_download(source_name, comfyui_path, downloader=None, skip_prompt=False):
    if not downloader:
        downloader = check_downloader()
        if not downloader:
            print("Error: Neither aria2c nor wget found. Please install one of them.")
            return False
            
    config_data, origin = get_source_config(source_name)
    
    if not config_data:
        print(f"Error: Could not load configuration for source '{source_name}'")
        return False

    if config_data is None:
        print(f"Error: Empty configuration for: {source_name}")
        return False

    downloads = []
    if isinstance(config_data, list):
        downloads = config_data
    elif isinstance(config_data, dict):
        downloads = config_data.get('downloads', [])
    
    if not downloads:
        print(f"Warning: No downloads found in {model_source_path}")
        return True

    source_name = source_name # kept for display
        
    print(f"\nSource: {source_name} ({origin})")
    print(f"ComfyUI Path: {comfyui_path}")
    
    # Show status tree before downloading
    print("\nFile status:")
    items_status = get_downloads_status(downloads, comfyui_path, fetch_remote_size=True)
    print_source_tree(source_name, items_status, indent="  ")
    print()

    # If all items are installed, we can skip or confirm
    all_installed = all(item['is_installed'] for item in items_status)
    if all_installed:
        print("All files are already installed.")
        return True

    # Calculate total download size
    total_download_size = 0
    for item in items_status:
        if not item['is_installed'] and item['remote_size']:
            total_download_size += item['remote_size']

    # Check disk space
    has_space, free_space = check_disk_space(comfyui_path, total_download_size)
    
    if total_download_size > 0:
        print(f"Total download size: {format_size(total_download_size)}")
        print(f"Free disk space: {format_size(free_space)}")
        
        if not has_space:
            print("Warning: Not enough disk space!")
            if not skip_prompt:
                 if not questionary.confirm("Warning: Not enough disk space. Proceed anyway?").ask():
                     return False
        
        if not skip_prompt:
            if not questionary.confirm("Do you want to proceed with the download?").ask():
                print("Aborted.")
                return False

    for item in items_status:
        if item['is_installed']:
            # print(f"Skipping existing file: {os.path.basename(item['dest'])}")
            continue
            
        full_dest = os.path.join(comfyui_path, item['dest'])
        download_file(item['url'], full_dest, downloader)
    return True

def handle_rm(model_sources, comfyui_path, force=False, dry_run=False):
    if not model_sources:
        # Interactive selection
        available_sources = get_available_sources()
        if not available_sources:
            print("No model sources available.")
            return
        
        model_sources = questionary.checkbox(
            "Select model sources to remove:",
            choices=available_sources
        ).ask()
        
        if not model_sources:
            print("No sources selected.")
            return

    for source_name in model_sources:
        config_data, _ = get_source_config(source_name)
        
        if not config_data:
            print(f"Error: Model source '{source_name}' not found.")
            continue
            
        print(f"\nProcessing removal for: {source_name}")
        
        # indent fix? No, just logic flow replacement
        pass
            
            
            
        downloads = []
        if isinstance(config_data, list):
            downloads = config_data
        elif isinstance(config_data, dict):
            downloads = config_data.get('downloads', [])
            
        if not downloads:
            print("No files to remove in this source.")
            continue
            
        files_to_delete = []
        total_size = 0
        
        for item in downloads:
            dest = item.get('dest')
            if not dest:
                continue
            full_path = os.path.join(comfyui_path, dest)
            if os.path.exists(full_path):
                if os.path.isfile(full_path):
                    size = os.path.getsize(full_path)
                    files_to_delete.append((full_path, size))
                    total_size += size
                else:
                    print(f"Warning: '{full_path}' exists but is a directory. Skipping.")
        
        if not files_to_delete:
            print("No installed files found for this source.")
            continue
            
        print("Files to be removed:")
        for path, size in files_to_delete:
            rel_path = os.path.relpath(path, comfyui_path)
            print(f"  - [{format_size(size):>10}] {rel_path}")
        
        print(f"\nTotal space to reclaim: {format_size(total_size)}")
        
        if dry_run:
            print("Dry run: skipping deletion.")
            continue
            
        if not force:
            confirmed = questionary.confirm(f"Are you sure you want to delete these {len(files_to_delete)} files?").ask()
            if not confirmed:
                print("Skipped.")
                continue
                
        for path, _ in files_to_delete:
            try:
                os.remove(path)
                rel_path = os.path.relpath(path, comfyui_path)
                print(f"Deleted: {rel_path}")
            except Exception as e:
                print(f"Error deleting {path}: {e}")

from .civitai import process_civitai_download

def list_sources_status(comfyui_path):
    sources = get_available_sources()
    if not sources:
        print("No model sources found.")
        return

    print(f"Installation status in: {comfyui_path}")
    print("Legend: [✓] Installed, [ ] Missing, [!] Partially Installed\n")
    
    for source_name in sources:
        config_data, _ = get_source_config(source_name)
        
        if not config_data:
            continue
            
        downloads = []
        if isinstance(config_data, list):
            downloads = config_data
        elif isinstance(config_data, dict):
            downloads = config_data.get('downloads', [])
            
        if not downloads:
            continue

        items_status = get_downloads_status(downloads, comfyui_path)
        
        installed_count = sum(1 for item in items_status if item['is_installed'])
        if installed_count == 0:
            continue

        print_source_tree(source_name, items_status, indent="  ")


def search_url_in_sources(url):
    """
    Search for a URL in all available model sources to find a suggested destination.
    Returns the folder path (dirname of dest) if found, else None.
    """
    sources = get_available_sources()
    for source in sources:
        config_data, _ = get_source_config(source)
        if not config_data:
            continue
            
        downloads = []
        if isinstance(config_data, list):
            downloads = config_data
        elif isinstance(config_data, dict):
            downloads = config_data.get('downloads', [])
            
        for item in downloads:
            if item.get('url') == url:
                dest = item.get('dest')
                if dest:
                    return os.path.dirname(dest)
    return None

def get_common_folders(comfyui_path):
    """
    Get a list of common model folders in ComfyUI path.
    Returns only folder names inside 'models' directory.
    """
    common = [
        "checkpoints",
        "loras",
        "vae",
        "controlnet",
        "upscale_models",
        "embeddings",
        "ipadapter",
        "clip",
        "unet",
        "vae_approx",
        "photomaker",
    ]
    
    # Also scan for any other directories in models/
    models_root = os.path.join(comfyui_path, "models")
    if os.path.exists(models_root):
        try:
            for item in os.listdir(models_root):
                path = os.path.join(models_root, item)
                if os.path.isdir(path):
                    if item not in common and not item.startswith("."):
                        common.append(item)
        except Exception:
            pass
            
    return sorted(common)

def handle_url_download(url, comfyui_path, target_dir=None, skip_prompt=False, downloader=None):
    from urllib.parse import urlparse, unquote
    
    if not downloader:
        downloader = check_downloader()
        if not downloader:
             print("Error: Neither aria2c nor wget found. Please install one of them.")
             return

    # Extract filename
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    filename = unquote(filename)
    
    if not filename:
        # Try to guess from content-disposition? 
        # For now, if no filename in URL, ask user or fail.
        # But most safetensors URLs have filename.
        print("Error: Could not determine filename from URL.")
        return

    # Determine target directory
    if not target_dir:
        # Search for suggestion
        suggested = search_url_in_sources(url)
        
        # If suggested is like "models/checkpoints", strip "models/"
        # We assume the default standard is inside models/
        if suggested and suggested.startswith("models/"):
            suggested = suggested[7:]
            
        choices = get_common_folders(comfyui_path)
        
        default_choice = None
        if suggested:
            if suggested not in choices:
                choices.append(suggested)
                choices.sort()
            default_choice = suggested
            
        # Interactive selection
        q = questionary.select(
            "Select destination folder:",
            choices=choices,
            default=default_choice if default_choice else None
        )
        selected_folder = q.ask()
        
        if not selected_folder:
            print("No folder selected. Aborting.")
            return
            
        # Construct path relative to ComfyUI/models
        # BUT wait, the user might have selected something that we extracted from 'models/' root
        # So we prepend 'models/'
        target_dir = os.path.join("models", selected_folder)
    
    # Construct full path
    full_dest_path = os.path.join(comfyui_path, target_dir, filename)
    
    # Check remote size and disk space
    print(f"\nTarget: {os.path.relpath(full_dest_path, comfyui_path)}")
    
    remote_size = get_remote_file_size(url)
    has_space = True
    free_space = 0
    
    if remote_size:
        has_space, free_space = check_disk_space(comfyui_path, remote_size)
        print(f"Download size: {format_size(remote_size)}")
        print(f"Free disk space: {format_size(free_space)}")
    else:
        print("Remote size: Unknown")
        # Check free space anyway just to show
        from .utils import get_free_disk_space
        free_space = get_free_disk_space(comfyui_path)
        print(f"Free disk space: {format_size(free_space)}")

    if not has_space:
        print("Warning: Not enough disk space!")
        if not skip_prompt:
             if not questionary.confirm("Warning: Not enough disk space. Proceed anyway?").ask():
                 return

    if not skip_prompt:
         if not questionary.confirm("Do you want to proceed with the download?").ask():
             print("Aborted.")
             return

    download_file(url, full_dest_path, downloader)
def main():
    parser = argparse.ArgumentParser(
        description="""ComfyDL: ComfyUI Model Downloader
https://github.com/ShinChven/comfydl

Usage:
  comfydl <source> [path]   Download a model source (e.g. 'flux')
  comfydl <subcommand> ...  Run a specific command""",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command")
    
    # Set command
    set_parser = subparsers.add_parser("set", help="Set configuration values")
    set_parser.add_argument("key", help="Configuration key (e.g., COMFYUI_ROOT, CIVITAI_TOKEN)")
    set_parser.add_argument("value", help="Configuration value")
    
    # Civitai command
    civitai_parser = subparsers.add_parser("civitai", help="Download model from Civitai by Model Version ID, URL, or AIR URN")
    civitai_parser.add_argument("version_id", help="Civitai Model Version ID (integer), Download URL, or AIR URN")
    civitai_parser.add_argument("comfyui_path", nargs="?", help="ComfyUI root directory override")
    civitai_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")

    # Sources command
    sources_parser = subparsers.add_parser("sources", help="List available model sources")
    sources_parser.add_argument("--installed", action="store_true", help="Show installation status in ComfyUI")

    sources_parser.add_argument("--comfyui_path", help="ComfyUI root directory override")

    # Registry command
    registry_parser = subparsers.add_parser("registry", help="Manage model registries")
    registry_subparsers = registry_parser.add_subparsers(dest="registry_command", required=True)

    # registry add
    reg_add = registry_subparsers.add_parser("add", help="Add a registry URL")
    reg_add.add_argument("url", help="URL of the registry JSON")
    reg_add.add_argument("--name", help="Optional name for the registry")

    # registry delete
    reg_del = registry_subparsers.add_parser("delete", help="Delete a registry")
    reg_del.add_argument("url", help="URL of the registry to delete")

    # registry list
    reg_list = registry_subparsers.add_parser("list", help="List configured registries")

    # registry update
    reg_update = registry_subparsers.add_parser("update", help="Update registries")
    reg_update.add_argument("registry_name", nargs="?", help="Specific registry name to update")


    # List command (local models)
    list_parser = subparsers.add_parser("list", help="List downloaded models in ComfyUI models directory")
    list_parser.add_argument("comfyui_path", nargs="?", help="ComfyUI root directory override")

    # Rm command
    rm_parser = subparsers.add_parser("rm", help="Remove models associated with a model source")
    rm_parser.add_argument("model_sources", nargs="*", help="Model source names to remove")
    rm_parser.add_argument("-f", "--force", action="store_true", help="Force removal without confirmation")
    rm_parser.add_argument("--dry-run", action="store_true", help="Show what would be removed without deleting")
    rm_parser.add_argument("--comfyui_path", help="ComfyUI root directory override")

    # To handle the existing "default" behavior (comfydl <source>), we check sys.argv
    # If the first argument is a known command, we parse.
    # Otherwise, we treat it as the legacy/default behavior.
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            parser.print_help()
            sys.exit(0)

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

            process_civitai_download(args.version_id, comfyui_path, skip_prompt=args.yes)
            return
        elif sys.argv[1] == "registry":
            args, _ = parser.parse_known_args()
            
            if args.registry_command == "add":
                url = args.url
                name = args.name
                if not name:
                    # Deduce name from URL filename
                    filename = os.path.basename(url)
                    if filename.lower().endswith('.json'):
                        name = filename[:-5]
                    else:
                        name = filename
                
                # Basic validation
                if not name:
                    print("Error: Could not determine registry name from URL. Please use --name.")
                    sys.exit(1)
                    
                add_registry(name, url)
                update_registry(name)
                
            elif args.registry_command == "delete":
                url = args.url
                # We store by name, so we need to find the name for this URL
                registries = get_registries()
                found_name = None
                for n, u in registries.items():
                    if u == url:
                        found_name = n
                        break
                
                if found_name:
                    remove_registry(found_name)
                    print(f"Registry '{found_name}' ({url}) removed.")
                    # delete cache file?
                    # we should delete the cache file too ideally
                    try:
                        from .config import get_registry_path
                        p = get_registry_path(found_name)
                        if p.exists():
                            os.remove(p)
                    except Exception:
                        pass
                else:
                    print(f"Error: Registry with URL '{url}' not found.")
                    
            elif args.registry_command == "list":
                registries = get_registries()
                if not registries:
                    print("No registries configured.")
                    # Check if default needs init
                    # init_registries() # auto init?
                    # registries = get_registries()
                
                if registries:
                     print("Configured Registries:")
                     for name, url in registries.items():
                         print(f"  - {name}: {url}")
            
            elif args.registry_command == "update":
                update_registry(args.registry_name)
            
            return
        elif sys.argv[1] == "sources":
            args, _ = parser.parse_known_args()
            if args.installed:
                comfyui_path = args.comfyui_path
                if not comfyui_path:
                    comfyui_path = get_config_value("COMFYUI_ROOT")
                
                if not comfyui_path:
                    print("Error: ComfyUI path not specified for --installed flag.")
                    sys.exit(1)
                
                comfyui_path = os.path.abspath(comfyui_path)
                if not os.path.exists(comfyui_path):
                    print(f"Error: ComfyUI directory '{comfyui_path}' does not exist.")
                    sys.exit(1)
                
                list_sources_status(comfyui_path)
            else:
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
        elif sys.argv[1] == "rm":
            args, _ = parser.parse_known_args()
            comfyui_path = args.comfyui_path
            if not comfyui_path:
                comfyui_path = get_config_value("COMFYUI_ROOT")
            
            if not comfyui_path:
                print("Error: ComfyUI path not specified.")
                sys.exit(1)
            
            comfyui_path = os.path.abspath(comfyui_path)
            handle_rm(args.model_sources, comfyui_path, force=args.force, dry_run=args.dry_run)
            return

    # If not a subcommand, use the original parser logic for sources
    parser = argparse.ArgumentParser(description="ComfyDL: ComfyUI Model Downloader\nhttps://github.com/ShinChven/comfydl")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("model_source", nargs="?", help="Model source name (e.g. 'flux') or path to YAML config")
    parser.add_argument("comfyui_path", nargs="?", help="ComfyUI root directory override")
    parser.add_argument("-d", "--directory", help="Target directory relative to ComfyUI root (e.g. models/checkpoints)")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    
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
        if args.model_source.startswith("urn:air:"):
            process_civitai_download(args.model_source, comfyui_path, skip_prompt=args.yes)
        elif args.model_source.startswith("http://") or args.model_source.startswith("https://"):
            handle_url_download(args.model_source, comfyui_path, target_dir=args.directory, skip_prompt=args.yes, downloader=downloader)
        else:
            process_download(args.model_source, comfyui_path, downloader, skip_prompt=args.yes)
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
             process_download(source_name, comfyui_path, downloader, skip_prompt=args.yes)

if __name__ == "__main__":
    main()
