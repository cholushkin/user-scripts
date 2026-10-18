import os
import sys
import json
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Shared")))

from base_script import BaseScript
from context import ParamGroup
from param import Param
from domain_utils import find_project_domain


DEFAULTS = {
    "log_level": 20,
    "log_file": None,

    "look_folders": "",
    "unity_dest_path": "",
    "music_configuration": "",
    "unity_root": "",
}


class ExportTracksScript(BaseScript):
    """
    Copies finished MP3 tracks (and a simplified metadata JSON for each one)
    from look_folders into a Unity project's asset folder.
    """

    def define_groups(self):
        return [
            ParamGroup("Export", [
                Param(
                    "look_folders",
                    str,
                    DEFAULTS["look_folders"],
                    description="Folders to search for track JSON configs (relative to --cwd, or absolute; semicolon-separated)"
                ),
                Param(
                    "unity_dest_path",
                    str,
                    DEFAULTS["unity_dest_path"],
                    description="Destination folder for the exported tracks, relative to the resolved Unity root"
                ),
                Param(
                    "music_configuration",
                    str,
                    DEFAULTS["music_configuration"],
                    description="Name of the music configuration asset to reference in each track's metadata JSON"
                ),
                Param(
                    "unity_root",
                    str,
                    DEFAULTS["unity_root"],
                    label="Unity project root (override)",
                    description="Optional. Blank = resolved via the discovered .uscript project's asset folder "
                                "(or root folder if no asset folder is configured)."
                ),
            ]),
        ]

    def get_defaults(self):
        return DEFAULTS

    def preview(self, ctx):
        return f"Export tracks -> {ctx['unity_dest_path']}"

    def _resolve(self, base, path):
        return path if os.path.isabs(path) else os.path.join(base, path)

    def _find_track_files(self, folders):
        files = []
        for folder in folders:
            if not os.path.isdir(folder):
                self.log_error(f"Folder not found: {folder}")
                continue

            self.log_debug(f"Searching for tracks in: {folder}")
            for root, _dirs, fnames in os.walk(folder):
                for fname in fnames:
                    if fname.lower().endswith(".json"):
                        files.append(os.path.join(root, fname))
        return files

    def _process_track(self, track_json_path, unity_dest_path, music_configuration):
        self.log_info(f"Processing track: {track_json_path}")

        try:
            with open(track_json_path, "r", encoding="utf-8") as f:
                track_data = json.load(f)
        except FileNotFoundError:
            self.log_error(f"JSON file not found: {track_json_path}. Skipping.")
            return
        except json.JSONDecodeError as e:
            self.log_error(f"Error decoding JSON: {track_json_path} - {e}. Skipping.")
            return
        except Exception as e:
            self.log_error(f"Error reading JSON file: {track_json_path} - {e}. Skipping.")
            return

        if "mix" not in track_data:
            self.log_error(f"'mix' section not found in JSON: {track_json_path}. Skipping.")
            return
        mix_config = track_data["mix"]

        export_params = track_data.get("export_parameters", {})
        if export_params.get("export", True) is False:
            self.log_info(f"Track not marked for export in JSON: {track_json_path}")
            return

        source_mp3_name = mix_config.get("output_file")
        if not source_mp3_name:
            self.log_error(f"'output_file' not found in 'mix' section of JSON: {track_json_path}. Skipping.")
            return

        source_mp3_path = os.path.join(os.path.dirname(track_json_path), source_mp3_name)
        if not os.path.exists(source_mp3_path):
            self.log_error(f"MP3 file not found: {source_mp3_path}. Skipping.")
            return

        dest_mp3_path = os.path.join(unity_dest_path, source_mp3_name)
        try:
            if os.path.exists(dest_mp3_path):
                self.log_warn(f"Overwriting existing file: {dest_mp3_path}")
            shutil.copy2(source_mp3_path, dest_mp3_path)
        except Exception as e:
            self.log_error(f"Error copying MP3: {source_mp3_path} to {dest_mp3_path} - {e}")
            return

        metadata = {
            "music_configuration": music_configuration,
            "tags": track_data.get("tags", {}),
        }
        dest_meta_path = os.path.join(unity_dest_path, os.path.splitext(source_mp3_name)[0] + ".meta.json")
        try:
            with open(dest_meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=4)
        except Exception as e:
            self.log_error(f"Error writing metadata JSON: {dest_meta_path} - {e}")
            return

        self.log_info(f"Successfully processed track: {source_mp3_name}")

    def run(self, ctx):
        extra = getattr(self.context, "extra", {})
        base = extra.get("cwd") or os.getcwd()

        look_folders = [f.strip() for f in ctx["look_folders"].split(";") if f.strip()]
        if not look_folders:
            self.log_error("look_folders is required")
            return
        abs_folders = [self._resolve(base, f) for f in look_folders]

        unity_dest_path = (ctx.get("unity_dest_path") or "").strip()
        if not unity_dest_path:
            self.log_error("unity_dest_path is required")
            return

        unity_root_override = (ctx.get("unity_root") or "").strip()
        if unity_root_override:
            unity_root = os.path.abspath(unity_root_override)
        else:
            info = find_project_domain(str(base))
            unity_root = info.get("asset_folder") or info.get("root_path")
            if not unity_root:
                self.log_error(
                    "Could not resolve a Unity project root. Set 'unity_root' explicitly, "
                    "or run inside a discovered '.uscript' project domain."
                )
                return
            unity_root = os.path.abspath(unity_root)

        unity_dest_abs = os.path.join(unity_root, unity_dest_path)
        os.makedirs(unity_dest_abs, exist_ok=True)

        self.log_info(f"Searching folders: {abs_folders}")
        self.log_info(f"Exporting to: {unity_dest_abs}")
        self.log_info(f"Music configuration tag: {ctx['music_configuration']}")

        track_files = self._find_track_files(abs_folders)
        if not track_files:
            self.log_warn("No track JSON files found.")
            return

        self.log_info(f"Found {len(track_files)} track JSON files to process.")
        for track_json_path in track_files:
            self._process_track(track_json_path, unity_dest_abs, ctx["music_configuration"])

        self.log_info("Export process complete.")


if __name__ == "__main__":
    ExportTracksScript().execute()
