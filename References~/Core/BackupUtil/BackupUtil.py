import os
import zipfile
import time
from datetime import datetime
from fnmatch import fnmatch
import sys

# Add Core to path so we can import ConfigManager, LogManager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from Core.ConfigManager import ConfigManager
from Core.LogManager import LogManager

class BackupUtil:
    def __init__(self, destination_path, folders, excludes=None):
        # Correcting the project root
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.destination_path = destination_path
        self.folders = [os.path.join(self.project_root, folder) for folder in folders]  # Correct the folder paths
        self.excludes = excludes or []

        # Replace {DATE} in destination path
        current_date = datetime.now().strftime("%Y-%m-%d")
        self.destination_zip = os.path.abspath(destination_path.replace("{DATE}", current_date))
        self.compression_level = zipfile.ZIP_DEFLATED

        # Load config
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.log_level = self.config.get("log_level", "balanced")
        self.log_manager = LogManager(self.log_level) # Initialize LogManager

        self.log_manager.log("verbose", "=== BackupUtil Initialized ===")
        self.log_manager.log("verbose", "Project root: " + self.project_root)
        self.log_manager.log("verbose", "Folders to backup:")
        for folder in self.folders:
            self.log_manager.log("verbose", "  -> " + folder)
        self.log_manager.log("verbose", "Exclude patterns: " + str(self.excludes))
        self.log_manager.log("verbose", "Destination zip path: " + self.destination_zip)
        self.log_manager.log("verbose", "Compression level: ZIP_DEFLATED")

    def is_excluded(self, filepath):
        rel_path = os.path.relpath(filepath, self.project_root)
        result = any(fnmatch(rel_path, pattern) for pattern in self.excludes)
        if result:
            self.log_manager.log("verbose", "Excluded by pattern: " + rel_path)
        return result

    def get_next_filename(self, filename):
        base, ext = os.path.splitext(filename)
        counter = 2
        new_filename = f"{base} ({counter}){ext}"
        while os.path.exists(new_filename):
            counter += 1
            new_filename = f"{base} ({counter}){ext}"
        self.log_manager.log("normal", "Existing backup found. New name: " + new_filename)
        return new_filename

    def backup(self):
        start_time = time.time()
        self.log_manager.log("normal", "Starting backup...")

        # Check if the folders exist
        for folder in self.folders:
            if not os.path.exists(folder):
                self.log_manager.log("important", "Error: Folder not found - " + folder)

        if os.path.exists(self.destination_zip):
            self.log_manager.log("normal", self.destination_zip + " already exists.")
            self.destination_zip = self.get_next_filename(self.destination_zip)

        os.makedirs(os.path.dirname(self.destination_zip), exist_ok=True)
        self.log_manager.log("normal", "Creating archive: " + self.destination_zip)

        total_files = 0
        with zipfile.ZipFile(self.destination_zip, 'w', self.compression_level) as zipf:
            for folder in self.folders:
                if not os.path.exists(folder):
                    self.log_manager.log("important", "Warning: Folder not found - " + folder)
                    continue
                for root, dirs, files in os.walk(folder):
                    self.log_manager.log("verbose", "Scanning directory: " + root)
                    for file in files:
                        full_path = os.path.join(root, file)
                        if not os.path.exists(full_path):
                            self.log_manager.log("verbose", "Skipped non-existent: " + full_path)
                            continue
                        if self.is_excluded(full_path):
                            continue
                        arcname = os.path.relpath(full_path, self.project_root)
                        zipf.write(full_path, arcname)
                        total_files += 1
                        self.log_manager.log("verbose", "Added: " + arcname)

        duration = time.time() - start_time
        self.log_manager.log("normal", "Backup complete: " + self.destination_zip)
        self.log_manager.log("normal", "Files added: " + str(total_files))
        self.log_manager.log("normal", "Duration: " + str(duration) + " seconds")

    def run(self):
        self.backup()