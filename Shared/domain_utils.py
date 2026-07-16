# Shared/domain_utils.py

import os
from typing import Optional, Tuple


def find_project_domain(start_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Traverses upward from start_path looking for a '.uscript' directory.
    
    Args:
        start_path: The starting file or directory path (e.g., current working directory or script path).
        
    Returns:
        A tuple of (project_name, uscript_dir_path) if found, otherwise (None, None).
    """
    if not start_path:
        start_path = os.getcwd()

    curr = os.path.abspath(start_path)

    # If start_path points to a file or non-existent path, start from its parent directory
    if os.path.isfile(curr) or not os.path.exists(curr):
        curr = os.path.dirname(curr)

    while True:
        candidate = os.path.join(curr, ".uscript")
        if os.path.isdir(candidate):
            # The project name is the name of the folder containing .uscript
            project_name = os.path.basename(curr.rstrip(os.sep)) or curr
            return project_name, candidate

        parent = os.path.dirname(curr)
        if parent == curr:  # Reached filesystem root
            break
        curr = parent

    return None, None