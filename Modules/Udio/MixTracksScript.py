import os
import sys
import json
import zipfile
import tempfile
import importlib.util
from fnmatch import fnmatch

from pydub import AudioSegment

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Shared")))

from base_script import BaseScript
from context import ParamGroup
from param import Param


EXPECTED_STEMS = ["bass.wav", "drums.wav", "other.wav", "vocals.wav"]

DEFAULTS = {
    "log_level": 20,
    "log_file": None,

    "look_folders": "",
    "override_target_wildcard": "",
    "override_json": "",
    "default_bitrate": "192k",
}


class MixTracksScript(BaseScript):
    """
    Finds track JSON configs under look_folders, extracts their stem ZIP
    archives, applies effects from Effects/, overlays the stems, and
    exports the final mix as MP3.
    """

    def define_groups(self):
        return [
            ParamGroup("Mix", [
                Param(
                    "look_folders",
                    str,
                    DEFAULTS["look_folders"],
                    description="Folders to search for track JSON configs (relative to --cwd, or absolute; semicolon-separated)"
                ),
                Param(
                    "override_target_wildcard",
                    str,
                    DEFAULTS["override_target_wildcard"],
                    label="Override: target wildcard",
                    description="Optional glob patterns (semicolon-separated) matched against each JSON filename. "
                                "Blank = override_json applies to every track."
                ),
                Param(
                    "override_json",
                    str,
                    DEFAULTS["override_json"],
                    label="Override: mix JSON",
                    description="Optional raw JSON object merged into each matched track's 'mix' section "
                                "(e.g. to force-disable 'ignore' for a batch re-mix)."
                ),
                Param(
                    "default_bitrate",
                    str,
                    DEFAULTS["default_bitrate"],
                    description="MP3 export bitrate used when a track's JSON doesn't specify one"
                ),
            ]),
        ]

    def get_defaults(self):
        return DEFAULTS

    def preview(self, ctx):
        return f"Mix tracks in [{ctx['look_folders']}]"

    def _resolve(self, base, path):
        return path if os.path.isabs(path) else os.path.join(base, path)

    def _find_track_json_files(self, folders):
        files = []
        for folder in folders:
            if not os.path.isdir(folder):
                self.log_error(f"Search folder not found: {folder}")
                continue

            self.log_debug(f"Searching for tracks in: {folder}")
            for root, _dirs, fnames in os.walk(folder):
                for fname in fnames:
                    if fname.lower().endswith(".json"):
                        files.append(os.path.join(root, fname))
        return files

    def _load_effects(self):
        effects_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Effects")
        effects = {}

        if not os.path.isdir(effects_path):
            self.log_error(f"Effects directory not found: {effects_path}")
            return effects

        self.log_debug(f"Loading effects from: {effects_path}")
        for filename in os.listdir(effects_path):
            if not filename.lower().endswith(".py") or filename == "__init__.py":
                continue

            effect_path = os.path.join(effects_path, filename)
            module_name = f"udio_effects.{os.path.splitext(filename)[0]}"

            try:
                spec = importlib.util.spec_from_file_location(module_name, effect_path)
                if not (spec and spec.loader):
                    self.log_warn(f"Could not create module spec for {filename}")
                    continue

                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                if hasattr(module, "effect_name") and isinstance(module.effect_name, dict):
                    for name, function in module.effect_name.items():
                        if not callable(function):
                            self.log_warn(f"Item '{name}' in 'effect_name' from {filename} is not callable.")
                            continue
                        if name in effects:
                            self.log_warn(f"Duplicate effect name '{name}' found in {filename}. Overwriting previous.")
                        effects[name] = function
                        self.log_debug(f"Loaded effect: '{name}' from {filename}")
                else:
                    self.log_warn(f"Effect module {filename} missing 'effect_name' dict.")

            except Exception as e:
                self.log_error(f"Error loading effect module {filename}: {e}")

        self.log_info(f"Loaded {len(effects)} effects: {', '.join(effects.keys())}")
        return effects

    def _apply_effects(self, track_data, effects_config, effects):
        for effect_name, effect_params in effects_config.items():
            effect_function = effects.get(effect_name)
            if not effect_function:
                self.log_warn(f"Effect '{effect_name}' not found. Skipping.")
                continue

            target_track = effect_params.get("target_track")
            params_for_effect = {k: v for k, v in effect_params.items() if k != "target_track"}

            targets = [target_track] if target_track else list(track_data.keys())
            for key in targets:
                if key not in track_data:
                    self.log_warn(f"Target track '{key}' for effect '{effect_name}' not found. Skipping effect.")
                    continue
                try:
                    track_data[key] = effect_function(track_data[key], **params_for_effect)
                except Exception as e:
                    self.log_error(f"Error applying effect '{effect_name}' to {key}: {e}")

    def _process_track(self, track_json_path, effects, mix_override, default_bitrate):
        self.log_info(f"Processing track from JSON: {track_json_path}")
        config_file_dir = os.path.dirname(track_json_path)

        try:
            with open(track_json_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except FileNotFoundError:
            self.log_error(f"JSON file not found: {track_json_path}")
            return False
        except json.JSONDecodeError as e:
            self.log_error(f"Error decoding JSON in: {track_json_path} - {e}")
            return False
        except Exception as e:
            self.log_error(f"Error reading JSON file {track_json_path}: {e}")
            return False

        track_config = config_data.get("mix")
        if not track_config or not isinstance(track_config, dict):
            self.log_warn(f"No 'mix' section found or it's not a dict in {track_json_path}. Skipping.")
            return False

        if mix_override:
            target_wildcards = mix_override.get("target_wildcard", [])
            apply_override = not target_wildcards
            if target_wildcards:
                base_name = os.path.basename(track_json_path)
                apply_override = any(fnmatch(base_name, w) for w in target_wildcards)

            if apply_override:
                track_config.update(mix_override.get("json", {}))

        if track_config.get("ignore", False):
            output_name = track_config.get("output_file", os.path.basename(track_json_path).replace(".json", ".mp3"))
            self.log_info(f"Skipping track {output_name} (ignore flag set)")
            return "ignored"

        source_zip_name = track_config.get("source_path")
        output_mp3_name = track_config.get("output_file")
        bitrate = track_config.get("bitrate", default_bitrate)

        if not source_zip_name or not output_mp3_name:
            self.log_error(f"Missing 'source_path' or 'output_file' in 'mix' section of {track_json_path}. Skipping.")
            return False

        source_zip_path = os.path.join(config_file_dir, source_zip_name)
        output_mp3_path = os.path.join(config_file_dir, output_mp3_name)

        if not os.path.exists(source_zip_path):
            self.log_error(f"Source ZIP file not found: {source_zip_path}")
            return False

        with tempfile.TemporaryDirectory(prefix="mix_") as temp_folder:
            try:
                with zipfile.ZipFile(source_zip_path, "r") as zip_ref:
                    zip_ref.extractall(temp_folder)
            except zipfile.BadZipFile:
                self.log_error(f"Invalid ZIP file: {source_zip_path}")
                return False
            except Exception as e:
                self.log_error(f"Error extracting ZIP file {source_zip_path}: {e}")
                return False

            track_data = {}
            missing_stems = []
            for stem_file in EXPECTED_STEMS:
                file_path = os.path.join(temp_folder, stem_file)
                if not os.path.exists(file_path):
                    missing_stems.append(stem_file)
                    continue
                try:
                    track_data[stem_file] = AudioSegment.from_wav(file_path)
                except Exception as e:
                    self.log_error(f"Error loading stem {stem_file} from {source_zip_path}: {e}")
                    missing_stems.append(f"{stem_file} (Load Error)")

            if missing_stems:
                self.log_error(
                    f"Missing required stems in {os.path.basename(source_zip_path)}: "
                    f"{', '.join(missing_stems)}. Skipping mix."
                )
                return False

            effects_config = track_config.get("effects", {})
            if effects_config:
                self._apply_effects(track_data, effects_config, effects)

            merged_audio = None
            for stem_name in EXPECTED_STEMS:
                if stem_name not in track_data:
                    continue
                if merged_audio is None:
                    merged_audio = track_data[stem_name]
                    continue
                try:
                    if merged_audio.frame_rate != track_data[stem_name].frame_rate:
                        track_data[stem_name] = track_data[stem_name].set_frame_rate(merged_audio.frame_rate)
                    merged_audio = merged_audio.overlay(track_data[stem_name])
                except Exception as e:
                    self.log_error(f"Error overlaying stem {stem_name}: {e}")
                    return False

            if merged_audio is None:
                self.log_warn(f"No audio data was successfully merged for {output_mp3_name}. Skipping export.")
                return False

            try:
                os.makedirs(os.path.dirname(output_mp3_path), exist_ok=True)
                merged_audio.export(output_mp3_path, format="mp3", bitrate=bitrate)
                self.log_info(f"Successfully exported: {output_mp3_name}")
            except Exception as e:
                self.log_error(f"Error exporting MP3 {output_mp3_path}: {e}")
                return False

        return True

    def run(self, ctx):
        extra = getattr(self.context, "extra", {})
        base = extra.get("cwd") or os.getcwd()

        look_folders = [f.strip() for f in ctx["look_folders"].split(";") if f.strip()]
        if not look_folders:
            self.log_error("look_folders is required")
            return

        abs_folders = [self._resolve(base, f) for f in look_folders]

        override_wildcards = [w.strip() for w in (ctx.get("override_target_wildcard") or "").split(";") if w.strip()]
        override_json_raw = (ctx.get("override_json") or "").strip()
        mix_override = None

        if override_json_raw:
            try:
                override_data = json.loads(override_json_raw)
            except json.JSONDecodeError as e:
                self.log_error(f"Invalid override_json: {e}")
                return
            mix_override = {"target_wildcard": override_wildcards, "json": override_data}
            self.log_info(f"Mix override active: {mix_override}")

        effects = self._load_effects()

        track_json_files = self._find_track_json_files(abs_folders)
        if not track_json_files:
            self.log_warn("No track JSON files found in the specified folders.")
            return

        self.log_info(f"Found {len(track_json_files)} potential track JSON files to process.")

        success_count = ignored_count = error_count = 0
        for json_file in track_json_files:
            result = self._process_track(json_file, effects, mix_override, ctx["default_bitrate"])
            if result is True:
                success_count += 1
            elif result == "ignored":
                ignored_count += 1
            else:
                error_count += 1

        self.log_info("Processing complete.")
        self.log_info(f"Successful mixes: {success_count}")
        self.log_info(f"Skipped (ignore flags): {ignored_count}")
        self.log_info(f"Errors/failed mixes: {error_count}")


if __name__ == "__main__":
    MixTracksScript().execute()
