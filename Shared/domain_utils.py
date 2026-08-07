# Shared/domain_utils.py

import os
import json
from typing import Dict

def find_project_domain(start_path: str) -> Dict:
    """
    Traverses upward from start_path looking for '.uscript' directories.
    The one containing a 'config.json' file is considered the project root.
    
    Returns a dictionary:
    {
        "project_name": str or None,
        "root_path": str or None,          # The project root (parent of the root .uscript)
        "asset_folder": str or None,       # Extracted from config.json
        "uscript_dirs": list of str        # All discovered .uscript folders (closest first)
    }
    """
    if not start_path:
        start_path = os.getcwd()

    curr = os.path.abspath(start_path)

    # If start_path points to a file or non-existent path, start from its parent directory
    if os.path.isfile(curr) or not os.path.exists(curr):
        curr = os.path.dirname(curr)

    uscript_dirs = []
    root_info = {
        "project_name": None,
        "root_path": None,
        "asset_folder": None,
        "uscript_dirs": uscript_dirs
    }

    while True:
        candidate_uscript = os.path.join(curr, ".uscript")
        
        if os.path.isdir(candidate_uscript):
            uscript_dirs.append(candidate_uscript)
            
            # Check if this .uscript contains the project configuration
            config_file = os.path.join(candidate_uscript, "config.json")
            if os.path.isfile(config_file) and root_info["root_path"] is None:
                root_info["root_path"] = curr
                root_info["project_name"] = os.path.basename(curr)
                
                # Prevent crashing on completely empty files (0 bytes)
                if os.path.getsize(config_file) == 0:
                    print(f"[WRN] Config file is empty at {config_file}. Using defaults.")
                else:
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            root_info["project_name"] = config.get("ProjectName", root_info["project_name"])
                            root_info["asset_folder"] = config.get("AssetFolder", "")
                    except Exception as e:
                        print(f"[ERR] Failed to parse config file at {config_file}: {e}")

        parent = os.path.dirname(curr)
        if parent == curr:  # Reached filesystem root
            break
        curr = parent

    return root_info