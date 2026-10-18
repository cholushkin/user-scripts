import os
import shutil
import json
import sys

# Add Core to path so we can import ConfigManager, LogManager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from Core.ConfigManager import ConfigManager
from Core.LogManager import LogManager


class ExportTracks:
    """
    Exports track files (MP3 and associated metadata JSON) from specified
    source folders to a Unity project's asset path. It reads track
    configurations from JSON files, copies the corresponding audio files,
    and creates a simplified metadata JSON file for use within Unity,
    including track tags and the music configuration name.
    """
    def __init__(self, look_folders, unity_dest_path, music_configuration, global_log_level=None):
        """
        Initializes the ExportTracks class.

        Args:
            look_folders (list): A list of folders to search for track files.
            unity_dest_path (str): The destination path within the Unity project
                                     to copy the tracks to. This path is relative
                                     to the Unity project root configured in config.json.
            music_configuration (str): The file name of the music configuration scriptable object
                                       where track metas will be added. This will be included in the
                                       metadata JSON for each track.
            global_log_level (str, optional): The global log level
                                     ("important", "normal", "verbose", "disabled").
                                     If None, it defaults to the value in the config file.
        """
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.look_folders = [os.path.join(self.project_root, folder) for folder in look_folders]
        self.music_configuration = music_configuration # Store the music configuration name

        # Initialize ConfigManager
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

        # Initialize LogManager
        self.log_manager = LogManager(self.config.get("log_level", "verbose"))
        if global_log_level is not None:
            self.log_manager.globalLogLevel = global_log_level

        self.unity_project_root = self.config.get("unity_project_root")
        if not self.unity_project_root:
            self.log_manager.log(
                "important",
                "❌ Unity project root is not set in the configuration. Please set the 'unity_project_root' in config.json.",
            )
            sys.exit(1)  # Exit if the Unity project root is not configured

        self.unity_project_root = os.path.join(self.project_root, self.unity_project_root)
        self.unity_dest_path = os.path.join(self.unity_project_root, unity_dest_path)
        os.makedirs(self.unity_dest_path, exist_ok=True)  # Ensure destination directory exists

    def _find_track_files(self):
        """Finds all track JSON files within the look_folders."""
        track_files = []
        for folder in self.look_folders:
            if not os.path.isdir(folder):
                self.log_manager.log("important", f"❌ Folder not found: {folder}")
                continue
            self.log_manager.log("verbose", f"📂 Searching for tracks in: {folder}")
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(".json"):
                        full_path = os.path.join(root, file)
                        track_files.append(full_path)
                        self.log_manager.log("verbose", f"    ✅ Found track JSON: {full_path}")
        return track_files

    def _process_track(self, track_json_path):
        """
        Processes a single track JSON file, copying the MP3 and creating metadata.

        Args:
            track_json_path (str): Path to the track JSON file.
        """
        self.log_manager.log("normal", f"\n▶️ Processing track: {track_json_path}")
        try:
            with open(track_json_path, "r", encoding="utf-8") as f:
                track_data = json.load(f)
        except FileNotFoundError:
            self.log_manager.log("important", f"❌ JSON file not found: {track_json_path}. Skipping.")
            return
        except json.JSONDecodeError as e:
            self.log_manager.log("important", f"❌ Error decoding JSON: {track_json_path} - {e}. Skipping.")
            return
        except Exception as e:
            self.log_manager.log("important", f"❌ Error reading JSON file: {track_json_path} - {e}. Skipping.")
            return

        # --- Check for 'mix' section and 'export' parameter ---
        if "mix" not in track_data:
            self.log_manager.log("important", f"❌ 'mix' section not found in JSON: {track_json_path}. Skipping.")
            return
        mix_config = track_data["mix"]

        export_params = track_data.get("export_parameters", {})
        if export_params.get("export", True) is False:  # Default to True if not present
            self.log_manager.log("normal", f"⏭️ Track not marked for export in JSON: {track_json_path}")
            return

        # --- Get MP3 source path ---
        source_mp3_name = mix_config.get("output_file")
        if not source_mp3_name:
            self.log_manager.log(
                "important", f"❌ 'output_file' not found in 'mix' section of JSON: {track_json_path}. Skipping."
            )
            return

        source_mp3_path = os.path.join(os.path.dirname(track_json_path), source_mp3_name)
        if not os.path.exists(source_mp3_path):
            self.log_manager.log("important", f"❌ MP3 file not found: {source_mp3_path}. Skipping.")
            return

        # --- Construct destination path and copy ---
        dest_mp3_path = os.path.join(self.unity_dest_path, source_mp3_name)
        try:
            if os.path.exists(dest_mp3_path):
                self.log_manager.log("normal", f"⚠️  Overwriting existing file: {dest_mp3_path}")
            shutil.copy2(source_mp3_path, dest_mp3_path)  # copy2 preserves metadata
            self.log_manager.log("verbose", f"    ✅ Copied MP3 to: {dest_mp3_path}")
        except Exception as e:
            self.log_manager.log("important", f"❌ Error copying MP3: {source_mp3_path} to {dest_mp3_path} - {e}")
            return

        # --- Create and save metadata JSON ---
        tags = track_data.get("tags", {})
        # Construct the metadata dictionary with the new format
        metadata = {
            "music_configuration": self.music_configuration,
            "tags": tags
        }
        dest_meta_path = os.path.join(self.unity_dest_path, os.path.splitext(source_mp3_name)[0] + ".meta.json")
        try:
            with open(dest_meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=4)
            self.log_manager.log("verbose", f"    ✅ Created metadata: {dest_meta_path}")
        except Exception as e:
            self.log_manager.log("important", f"❌ Error writing metadata JSON: {dest_meta_path} - e")
            return

        self.log_manager.log("normal", f"    ✅ Successfully processed track: {source_mp3_name}")

    def run(self):
        """Finds and processes all track JSON files."""
        self.log_manager.log("important", "=" * 40)
        self.log_manager.log("important", "🚀 Starting Export Tracks to Unity")
        self.log_manager.log("important", f"Project Root: {self.project_root}")
        self.log_manager.log("important", f"Searching Folders: {self.look_folders}")
        self.log_manager.log("important", f"Exporting to: {self.unity_dest_path}")
        self.log_manager.log("important", f"Music Configuration Tag: {self.music_configuration}") # Log the config name
        self.log_manager.log("important", "=" * 40)

        track_json_files = self._find_track_files()
        if not track_json_files:
            self.log_manager.log("important", "⏹️ No track JSON files found.")
            return

        self.log_manager.log("normal", f"ℹ️ Found {len(track_json_files)} track JSON files to process.")
        for track_json_path in track_json_files:
            self._process_track(track_json_path)
        self.log_manager.log("important", "🏁 Export process complete.")
