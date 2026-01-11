import os
import json
import requests
from pathlib import Path
from .config import get_registries, add_registry, get_registry_path, get_config_value, remove_registry

DEFAULT_REGISTRY_URL = "https://shinchven.github.io/comfydl-sources/sources.json"
DEFAULT_REGISTRY_NAME = "default"

def init_registries():
    """Ensure default registry exists in config."""
    registries = get_registries()
    if not registries:
        add_registry(DEFAULT_REGISTRY_NAME, DEFAULT_REGISTRY_URL)
        return True
    return False

def update_registry(name=None):
    """
    Update local cache of registries.
    If name is provided, update only that registry.
    Otherwise update all.
    """
    init_registries()
    registries = get_registries()
    
    to_update = []
    if name:
        if name in registries:
            to_update.append((name, registries[name]))
        else:
            print(f"Error: Registry '{name}' not configured.")
            return False
    else:
        to_update = list(registries.items())
        
    success = True
    for reg_name, url in to_update:
        print(f"Updating registry '{reg_name}' from {url}...")
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Validate structure? For now we assume it's a list or dict of sources
            # actually the format is likely { "source_name": { ... }, ... } or similar
            # Wait, the user said "the sources.json file fill be downloaded to local as <registry_name>.json"
            # It seems the content of sources.json IS the registry content.
            
            dest_path = get_registry_path(reg_name)
            with open(dest_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  ✓ Updated {reg_name}")
        except Exception as e:
            print(f"  ✗ Failed to update {reg_name}: {e}")
            success = False
            
    return success

def load_registry_sources():
    """
    Load all sources from all local registry files.
    Returns a dict {source_name: {config...}, ...}
    Later registries overwrite earlier ones? Or maybe we prefix? 
    For now, let's merge, but maybe warn on collision?
    Actually, let's just merge.
    """
    registries = get_registries()
    all_sources = {}
    
    # Order matters? Maybe sorted by name?
    for name in registries:
        path = get_registry_path(name)
        if not path.exists():
            continue
            
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                
            # data structure: The user said "sources.json" contains the sources. 
            # If it's the repo linked (comfydl-sources), let's assume it's a dict where keys are source names.
            if isinstance(data, dict):
                # Check if wrapped in 'sources' key
                sources_dict = data.get('sources', data)
                
                # If sources_dict is not a dict (e.g. string version), skip
                if not isinstance(sources_dict, dict):
                    print(f"Warning: Invalid registry format for '{name}'. Expected dict of sources.")
                    continue

                for source_name, source_config in sources_dict.items():
                    all_sources[source_name] = source_config
            elif isinstance(data, list):
                # What if it is a list? 
                pass
                
        except Exception as e:
            print(f"Warning: Failed to load registry '{name}': {e}")
            
    return all_sources

def resolve_registry_source(source_name):
    """
    Look for a source in the loaded registries.
    Returns config dict if found, else None.
    """
    sources = load_registry_sources()
    return sources.get(source_name)
