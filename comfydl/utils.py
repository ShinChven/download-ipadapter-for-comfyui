import os
import shutil
import subprocess
import sys
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from .config import get_config_value

def append_civitai_token(url):
    if "civitai.com" not in url:
        return url
    
    token = get_config_value("CIVITAI_TOKEN")
    if not token:
        return url
        
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    
    if 'token' in query:
        return url # Token already present
        
    query['token'] = token
    new_query = urlencode(query, doseq=True)
    
    parsed = parsed._replace(query=new_query)
    return urlunparse(parsed)

def check_downloader():
    if shutil.which("aria2c"):
        return "aria2c"
    elif shutil.which("wget"):
        return "wget"
    else:
        return None

def download_file(url, filepath, downloader):
    filename = os.path.basename(filepath)
    directory = os.path.dirname(filepath)
    
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        
    if os.path.exists(filepath):
        print(f"Skipping existing file: {filename}")
        return

    print(f"Downloading {filename}...")
    
    # Process URL for Civitai
    final_url = append_civitai_token(url)
    
    try:
        if downloader == "aria2c":
            cmd = [
                "aria2c", "-x", "16", "-s", "16", "-k", "1M",
                "--console-log-level=warn", "-c",
                "-d", directory, "-o", filename, final_url
            ]
            if "huggingface.co" in final_url:
                hf_token = get_config_value("HF_TOKEN")
                if hf_token:
                    cmd.insert(-1, f"--header=Authorization: Bearer {hf_token}")
        elif downloader == "wget":
            cmd = ["wget", "-c", "-O", filepath]
            
            if "huggingface.co" in final_url:
                hf_token = get_config_value("HF_TOKEN")
                if hf_token:
                    cmd.append(f"--header=Authorization: Bearer {hf_token}")
                    cmd.append("--content-disposition")

            cmd.append(final_url)
        else:
            # Fallback to python requests if needed, but for now we error or just warn
            print("Error: No external downloader found (aria2c/wget).")
            return
            
        subprocess.run(cmd, check=True)
        print(f"{filename} downloaded successfully.")
        
    except subprocess.CalledProcessError:
        print(f"Error downloading {filename}.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
