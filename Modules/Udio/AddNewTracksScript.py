import os
import re
import sys
import json
import copy
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Shared")))

from base_script import BaseScript
from context import ParamGroup
from param import Param


DEFAULTS = {
    "log_level": 20,
    "log_file": None,

    "source_directory": "",
    "track_target_path": "",
    "move_files": True,
}


class AddNewTracksScript(BaseScript):
    """
    Moves or copies MP3/ZIP file pairs from a source directory into numbered
    per-track subfolders, generating a default track JSON config for each one
    from the bundled AddNewTracksJsonTemplate.json.
    """

    def define_groups(self):
        return [
            ParamGroup("Tracks", [
                Param(
                    "source_directory",
                    str,
                    DEFAULTS["source_directory"],
                    description="Folder containing the raw .mp3/.zip pairs (relative to --cwd, or absolute)"
                ),
                Param(
                    "track_target_path",
                    str,
                    DEFAULTS["track_target_path"],
                    description="Folder where per-track subfolders are created (relative to --cwd, or absolute)"
                ),
                Param(
                    "move_files",
                    bool,
                    DEFAULTS["move_files"],
                    description="If true, moves the source files; if false, copies them"
                ),
            ]),
        ]

    def get_defaults(self):
        return DEFAULTS

    def preview(self, ctx):
        return f"Ingest {ctx['source_directory']} -> {ctx['track_target_path']}"

    def _resolve(self, base, path):
        return path if os.path.isabs(path) else os.path.join(base, path)

    def _load_json_template(self):
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AddNewTracksJsonTemplate.json")
        if not os.path.exists(template_path):
            self.log_error(f"JSON template file not found at '{template_path}'.")
            return None
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.log_error(f"Invalid JSON in template file '{template_path}': {e}")
            return None

    def _create_track_json(self, track_target_path, folder_name, track_name, json_template):
        if json_template is None:
            return

        json_file_name = f"{track_name}.json"
        dest_json_path = os.path.join(track_target_path, folder_name, json_file_name)

        updated_template = copy.deepcopy(json_template)
        updated_template["mix"]["source_path"] = f"{track_name}.zip"
        updated_template["mix"]["output_file"] = f"{track_name}.mp3"

        try:
            with open(dest_json_path, "w", encoding="utf-8") as f:
                json.dump(updated_template, f, indent=4)
            self.log_info(f"Created JSON file: {os.path.join(folder_name, json_file_name)}")
        except Exception as e:
            self.log_error(f"Could not create JSON file '{dest_json_path}': {e}")

    def run(self, ctx):
        extra = getattr(self.context, "extra", {})
        base = extra.get("cwd") or os.getcwd()

        source_directory = (ctx.get("source_directory") or "").strip()
        track_target_path = (ctx.get("track_target_path") or "").strip()

        if not source_directory or not track_target_path:
            self.log_error("source_directory and track_target_path are both required")
            return

        source_path = self._resolve(base, source_directory)
        track_target_path = self._resolve(base, track_target_path)
        move_files = bool(ctx["move_files"])

        action_word = "Moved" if move_files else "Copied"
        file_operation = shutil.move if move_files else shutil.copy2
        count_description = "Files moved" if move_files else "Files copied"

        self.log_info(f"Source directory: {source_path}")
        self.log_info(f"Target root directory: {track_target_path}")
        self.log_info(f"Mode: {'Move files' if move_files else 'Copy files'}")

        files_processed_count = 0
        folders_created_count = 0

        if not os.path.isdir(track_target_path):
            try:
                os.makedirs(track_target_path)
                self.log_info(f"Created target root directory: {track_target_path}")
                folders_created_count += 1
            except OSError as e:
                self.log_error(f"Could not create target root directory '{track_target_path}'. {e}")
                return

        json_template = self._load_json_template()

        try:
            all_items = os.listdir(source_path)
        except OSError as e:
            self.log_error(f"Could not read source directory '{source_path}'. {e}")
            return

        basenames_mp3, basenames_zip = set(), set()
        for name in all_items:
            full_path = os.path.join(source_path, name)
            if not os.path.isfile(full_path):
                continue
            stem, ext = os.path.splitext(name)
            ext_lower = ext.lower()
            if ext_lower == ".mp3":
                basenames_mp3.add(stem)
            elif ext_lower == ".zip":
                basenames_zip.add(stem)

        inconsistent = basenames_mp3.symmetric_difference(basenames_zip)
        if inconsistent:
            self.log_error("File inconsistency detected: '.mp3' without matching '.zip' or vice-versa.")
            for base_name in inconsistent:
                if base_name in basenames_mp3:
                    self.log_error(f"  Found '{base_name}.mp3' without matching '.zip'")
                else:
                    self.log_error(f"  Found '{base_name}.zip' without matching '.mp3'")
            return

        valid_basenames = basenames_mp3.intersection(basenames_zip)
        if not valid_basenames:
            self.log_warn("No MP3/ZIP pairs found in the source directory.")
            return

        self.log_info(f"Found {len(valid_basenames)} valid MP3/ZIP pairs for processing.")

        for base_name_extless in sorted(valid_basenames):
            source_mp3 = base_name_extless + ".mp3"
            source_zip = base_name_extless + ".zip"
            source_mp3_full_path = os.path.join(source_path, source_mp3)
            source_zip_full_path = os.path.join(source_path, source_zip)

            if not os.path.exists(source_mp3_full_path) or not os.path.exists(source_zip_full_path):
                self.log_warn(f"Source file(s) for '{base_name_extless}' disappeared before processing. Skipping.")
                continue

            match = re.match(r"^(.*?)(?: \(\d+\))?$", base_name_extless)
            folder_name = match.group(1).strip() if match else base_name_extless.strip()
            dest_folder_path = os.path.join(track_target_path, folder_name)

            if not os.path.isdir(dest_folder_path):
                try:
                    os.makedirs(dest_folder_path)
                    self.log_debug(f"Subfolder created: {folder_name}")
                    folders_created_count += 1
                except OSError as e:
                    self.log_error(f"Could not create subfolder '{dest_folder_path}'. Skipping '{base_name_extless}'. {e}")
                    continue

            next_number = 1
            try:
                existing_files = os.listdir(dest_folder_path)
                max_num = 0
                pattern = re.compile(r"^" + re.escape(folder_name) + r" (\d+)\.(mp3|zip)$", re.IGNORECASE)
                for fname in existing_files:
                    m = pattern.match(fname)
                    if m:
                        max_num = max(max_num, int(m.group(1)))
                next_number = max_num + 1
            except OSError as e:
                self.log_error(f"Could not read destination subfolder '{dest_folder_path}'. Skipping '{base_name_extless}'. {e}")
                continue

            new_mp3_name = f"{folder_name} {next_number}.mp3"
            new_zip_name = f"{folder_name} {next_number}.zip"
            dest_mp3_path = os.path.join(dest_folder_path, new_mp3_name)
            dest_zip_path = os.path.join(dest_folder_path, new_zip_name)

            try:
                file_operation(source_mp3_full_path, dest_mp3_path)
                self.log_info(f"{action_word} {source_mp3} -> {os.path.join(folder_name, new_mp3_name)}")
                files_processed_count += 1

                track_name = f"{folder_name} {next_number}"
                self._create_track_json(track_target_path, folder_name, track_name, json_template)

                try:
                    if not os.path.exists(source_zip_full_path):
                        self.log_error(
                            f"Source ZIP '{source_zip}' disappeared before it could be {action_word.lower()}. "
                            f"MP3 was already {action_word.lower()}."
                        )
                        if not move_files and os.path.exists(dest_mp3_path):
                            os.remove(dest_mp3_path)
                            files_processed_count -= 1
                    else:
                        file_operation(source_zip_full_path, dest_zip_path)
                        self.log_info(f"{action_word} {source_zip} -> {os.path.join(folder_name, new_zip_name)}")
                        files_processed_count += 1

                except Exception as e_zip:
                    self.log_error(f"Failed to {action_word.lower()} ZIP file '{source_zip}' after {action_word.lower()}ing MP3. {e_zip}")
                    if not move_files and os.path.exists(dest_mp3_path):
                        os.remove(dest_mp3_path)
                        files_processed_count -= 1

            except Exception as e_mp3:
                self.log_error(f"Failed to {action_word.lower()} MP3 file '{source_mp3}'. Skipping pair. {e_mp3}")

        self.log_info("Processing complete.")
        self.log_info(f"{count_description}: {files_processed_count}")
        self.log_info(f"Subfolders created: {folders_created_count}")


if __name__ == "__main__":
    AddNewTracksScript().execute()
