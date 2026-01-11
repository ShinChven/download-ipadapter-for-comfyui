import os
import yaml
from pathlib import Path

CONFIG_FILE = Path.home() / ".comfydl_config"

def load_config():
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Could not load config file: {e}")
        return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(config, f)
    except Exception as e:
        print(f"Error: Could not save config file: {e}")

def set_config_value(key, value):
    config = load_config()
    config[key] = value
    save_config(config)
    print(f"Configuration saved: {key} = {value}")

def get_config_value(key):
    config = load_config()
    return config.get(key)

def get_registries():
    config = load_config()
    registries = config.get("registries", {})
    # Ensure default exists if not present (only if config was empty or missing default)
    # Actually, main.py/registry logic might handle initialization, but good to have a getter.
    return registries

def add_registry(name, url):
    config = load_config()
    if "registries" not in config:
        config["registries"] = {}
    config["registries"][name] = url
    save_config(config)

def remove_registry(name):
    config = load_config()
    if "registries" in config and name in config["registries"]:
        del config["registries"][name]
        save_config(config)
        return True
    return False

def get_registry_path(name):
    registries_dir = Path.home() / ".comfydl" / "registries"
    registries_dir.mkdir(parents=True, exist_ok=True)
    return registries_dir / f"{name}.json"
