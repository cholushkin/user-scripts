import os
import zipfile
import json
import shutil
import importlib.util
import tempfile
import traceback
from pydub import AudioSegment
import sys
from fnmatch import fnmatch

# Add Core to path so we can import ConfigManager, LogManager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from Core.ConfigManager import ConfigManager
from Core.LogManager import LogManager

# --- Script Configuration ---
EXPECTED_STEMS = ["bass.wav", "drums.wav", "other.wav", "vocals.wav"]
DEFAULT_BITRATE = "192k"

class MixTracks:
    """
    Processes track configurations from JSON files, mixes audio stems from
    associated ZIP archives, applies defined effects, and exports the final
    mix as an MP3. Supports overriding mix parameters via a dictionary
    and skipping tracks based on configuration.
    """
    def __init__(self, look_folders, global_log_level=None, mix_override=None):
        """
        Initializes the MixTracks processor.

        Args:
            look_folders (list[str]): List of directory paths (relative to project root)
                                      to search for track subfolders.
            global_log_level (str, optional): Desired logging level ('verbose', 'normal', 'important').
                                              Defaults to config file setting or 'verbose'.
            mix_override (dict, optional): A dictionary to override 'mix' section values in the JSON.
                                           Can include "target_wildcard" (list of glob patterns)
                                           and "json" (dictionary of override values).
        """
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.look_folders = [os.path.join(self.project_root, folder) for folder in look_folders]
        self.mix_override = mix_override  # Store the mix override

        # Initialize ConfigManager
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

        # Initialize LogManager (using the provided snippet)
        self.log_manager = LogManager(self.config.get("log_level", "verbose"))
        if global_log_level != None:
            self.log_manager.globalLogLevel = global_log_level

        # Effects path, relative to the current script's directory
        self.effects_path = os.path.join(os.path.dirname(__file__), "Effects")
        self.effects = self._load_effects()

    def _find_track_json_files(self):
        """Finds all track JSON files (e.g., 'Track Name 1.json') within the look_folders."""
        json_files = []
        for folder in self.look_folders:
            if not os.path.isdir(folder):
                self.log_manager.log("important", f"❌ Search folder not found: {folder}")
                continue
            self.log_manager.log("verbose", f"📂 Searching for tracks in: {folder}")
            for root, _, files in os.walk(folder):
                for file in files:
                    # Process any .json file, assuming it's a track config
                    if file.lower().endswith(".json"):
                        full_path = os.path.join(root, file)
                        json_files.append(full_path)
                        self.log_manager.log("verbose", f"    ✅ Mapped JSON: {full_path}")
        return json_files

    def _load_effects(self):
        """Loads effect functions from Python files in the Effects directory."""
        effects = {}
        if not os.path.isdir(self.effects_path):
            self.log_manager.log("important", f"❌ Effects directory not found: {self.effects_path}")
            return effects

        self.log_manager.log("normal", f"🔍 Loading effects from: {self.effects_path}")
        for filename in os.listdir(self.effects_path):
            if filename.lower().endswith(".py") and filename != "__init__.py":
                effect_path = os.path.join(self.effects_path, filename)
                module_name = f"effects.{os.path.splitext(filename)[0]}"  # Unique module name
                try:
                    spec = importlib.util.spec_from_file_location(module_name, effect_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = module  # Add to sys.modules before exec
                        spec.loader.exec_module(module)

                        # Corrected Effect Loading Logic
                        if hasattr(module, "effect_name") and isinstance(module.effect_name, dict):
                            for name, function in module.effect_name.items():
                                if callable(function):
                                    if name in effects:
                                        self.log_manager.log("important",
                                                             f"⚠️ Duplicate effect name '{name}' found in {filename}. Overwriting previous.")
                                    effects[name] = function
                                    self.log_manager.log("verbose", f"    ✅ Loaded effect: '{name}' from {filename}")
                                else:
                                    self.log_manager.log("important",
                                                         f"⚠️ Item '{name}' in 'effect_name' from {filename} is not callable.")
                        else:
                            self.log_manager.log("important",
                                                 f"⚠️ Effect module {filename} missing 'effect_name' dictionary or it's not a dictionary.")
                    else:
                        self.log_manager.log("important", f"⚠️ Could not create module spec for {filename}")

                except Exception as e:
                    self.log_manager.log("important", f"❌ Error loading effect module {filename}: {e}\n{traceback.format_exc()}")
        self.log_manager.log("normal", f"✨ Loaded {len(effects)} effects: {', '.join(effects.keys())}")
        return effects

    def process_track(self, track_json_path):
        """
        Processes a single track based on its JSON configuration file.
        Returns True on success, "ignored" if explicitly ignored, False on error.
        """
        self.log_manager.log("normal", f"\n▶️ Processing track from JSON: {track_json_path}")
        config_file_dir = os.path.dirname(track_json_path)

        try:
            with open(track_json_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except FileNotFoundError:
            self.log_manager.log("important", f"❌ JSON file not found: {track_json_path}")
            return False
        except json.JSONDecodeError as e:
            self.log_manager.log("important", f"❌ Error decoding JSON in: {track_json_path} - {e}")
            return False
        except Exception as e:
            self.log_manager.log("important", f"❌ Error reading JSON file {track_json_path}: {e}")
            return False

        # --- Get Mix Configuration ---
        track_config = config_data.get("mix")
        if not track_config or not isinstance(track_config, dict):
            self.log_manager.log("important",
                            f"⚠️ No 'mix' section found or it's not a dictionary in {track_json_path}. Skipping.")
            return False  # Treat as skippable failure

        # --- Apply Overrides ---
        if self.mix_override:
            # Check for target_wildcard
            target_wildcards = self.mix_override.get("target_wildcard", [])
            apply_override = False
            if target_wildcards:
                base_name = os.path.basename(track_json_path)
                for wildcard in target_wildcards:
                    if fnmatch(base_name, wildcard):
                        self.log_manager.log("verbose", f"    ✅ Matched target_wildcard '{wildcard}' for {base_name}. Applying override.")
                        apply_override = True
                        break  # Apply only once if matched
            else: # apply if no wildcards specified in override
                 self.log_manager.log("verbose", f"    ✅ No target_wildcard specified in override. Applying override to {os.path.basename(track_json_path)}.")
                 apply_override = True

            if apply_override:
                 # Use a copy to avoid modifying the original dictionary while iterating or updating
                 override_json_data = self.mix_override.get("json", {}).copy()
                 track_config.update(override_json_data) # Override the mix section


        # --- Check Ignore Flag (after overrides) ---
        if track_config.get("ignore", False):
            output_name = track_config.get('output_file', os.path.basename(track_json_path).replace('.json', '.mp3'))
            self.log_manager.log("normal", f"⏭️ Skipping track {output_name} (ignore flag set in JSON after overrides)")
            return "ignored"  # Indicate explicit skip

        # --- Get Paths and Parameters ---
        source_zip_name = track_config.get("source_path")
        output_mp3_name = track_config.get("output_file")
        bitrate = track_config.get("bitrate", DEFAULT_BITRATE)

        if not source_zip_name or not output_mp3_name:
            self.log_manager.log("important",
                            f"❌ Missing 'source_path' or 'output_file' in 'mix' section of {track_json_path}. Skipping.")
            return False

        source_zip_path = os.path.join(config_file_dir, source_zip_name)
        output_mp3_path = os.path.join(config_file_dir, output_mp3_name)

        if not os.path.exists(source_zip_path):
            self.log_manager.log("important", f"❌ Source ZIP file not found: {source_zip_path}")
            return False

        # --- Process Track ---
        with tempfile.TemporaryDirectory(prefix="mix_") as temp_folder:
            self.log_manager.log("verbose", f"    📦 Extracting {source_zip_name} to {temp_folder}")

            # Extract ZIP file
            try:
                with zipfile.ZipFile(source_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_folder)
            except zipfile.BadZipFile:
                self.log_manager.log("important", f"❌ Invalid ZIP file: {source_zip_path}")
                return False
            except Exception as e:
                self.log_manager.log("important", f"❌ Error extracting ZIP file {source_zip_path}: {e}")
                return False

            # Load expected audio stems and check for missing ones
            track_data = {}
            loaded_stems = []
            missing_stems = []
            for stem_file in EXPECTED_STEMS:  # Use defined order
                file_path = os.path.join(temp_folder, stem_file)
                if os.path.exists(file_path):
                    try:
                        track_data[stem_file] = AudioSegment.from_wav(file_path)
                        loaded_stems.append(stem_file)
                        self.log_manager.log("verbose", f"    🔊 Loaded stem: {stem_file}")
                    except Exception as e:
                        # Treat loading error as a missing stem for simplicity
                        self.log_manager.log("important",
                                             f"❌ Error loading stem {stem_file} from {source_zip_path}: {e}")
                        missing_stems.append(f"{stem_file} (Load Error)")
                else:
                    missing_stems.append(stem_file)

            # --- Strict Stem Check ---
            if missing_stems:
                self.log_manager.log("important",
                                     f"❌ Missing required stems in {source_zip_name}: {', '.join(missing_stems)}. Skipping mix.")
                return False  # Quit processing this track due to missing stems

            self.log_manager.log("verbose", f"    🔊 All expected stems loaded: {', '.join(loaded_stems)}")

            # Apply effects dynamically
            effects_config = track_config.get("effects", {})
            if effects_config:
                self.log_manager.log("verbose", f"    ✨ Applying Effects...")
                for effect_name, effect_params in effects_config.items():
                    if effect_name in self.effects:
                        target_track = effect_params.get("target_track", None)
                        effect_function = self.effects[effect_name]
                        params_for_effect = {k: v for k, v in effect_params.items() if k != "target_track"}

                        if target_track:
                            if target_track in track_data:
                                self.log_manager.log("verbose",
                                                     f"      Applying '{effect_name}' to {target_track} with params: {params_for_effect}")
                                try:
                                    track_data[target_track] = effect_function(track_data[target_track],
                                                                               **params_for_effect)
                                except Exception as e:
                                    self.log_manager.log("important",
                                                         f"❌ Error applying effect '{effect_name}' to {target_track}: {e}\n{traceback.format_exc()}")
                                    # Decide if error is fatal for the track: return False
                            else:
                                self.log_manager.log("important",
                                                     f"⚠️ Target track '{target_track}' for effect '{effect_name}' not found. Skipping effect.")
                        else:
                            self.log_manager.log("verbose",
                                                 f"      Applying '{effect_name}' to all stems with params: {params_for_effect}")
                            for key in list(track_data.keys()):
                                try:
                                    track_data[key] = effect_function(track_data[key], **params_for_effect)
                                except Exception as e:
                                    self.log_manager.log("important",
                                                         f"❌ Error applying effect '{effect_name}' to {key}: {e}\n{traceback.format_exc()}")
                                    # Decide if error is fatal for the track: return False
                    else:
                        self.log_manager.log("important", f"⚠️ Effect '{effect_name}' not found. Skipping.")
            else:
                self.log_manager.log("verbose", "    ✨ No effects specified in JSON.")

            # Merge tracks (overlay method)
            self.log_manager.log("verbose", "    🔄 Merging loaded stems...")
            merged_audio = None
            first_stem = True
            for stem_name in EXPECTED_STEMS:  # Use defined order
                if stem_name in track_data:
                    if first_stem:
                        merged_audio = track_data[stem_name]
                        first_stem = False
                        self.log_manager.log("verbose", f"      Base for merge: {stem_name}")
                    else:
                        try:
                            # Ensure both audio segments have the same frame rate before overlay
                            if merged_audio.frame_rate != track_data[stem_name].frame_rate:
                                self.log_manager.log("verbose", f"        Resampling {stem_name} to match base frame rate {merged_audio.frame_rate}")
                                track_data[stem_name] = track_data[stem_name].set_frame_rate(merged_audio.frame_rate)

                            merged_audio = merged_audio.overlay(track_data[stem_name])
                            self.log_manager.log("verbose", f"      Overlayed: {stem_name}")
                        except Exception as e:
                            self.log_manager.log("important", f"❌ Error overlaying stem {stem_name}: {e}")
                            return False  # Treat overlay error as fatal for this mix

            # Export final MP3
            if merged_audio:
                self.log_manager.log("normal",
                                     f"    💾 Exporting final MP3: {output_mp3_path} (Bitrate: {bitrate})")
                try:
                    os.makedirs(os.path.dirname(output_mp3_path), exist_ok=True)
                    merged_audio.export(output_mp3_path, format="mp3", bitrate=bitrate)
                    self.log_manager.log("important", f"✅ Successfully exported: {output_mp3_name}")
                except Exception as e:
                    self.log_manager.log("important",
                                         f"❌ Error exporting MP3 {output_mp3_path}: {e}\n{traceback.format_exc()}")
                    return False  # Export failed
            else:
                self.log_manager.log("important",
                                     f"⚠️ No audio data was successfully merged for {output_mp3_name}. Skipping export.")
                return False  # Nothing to export is a failure condition

        self.log_manager.log("verbose", f"    🧹 Cleaned up temporary files for {source_zip_name}")
        return True  # Indicate success for this track


    def run(self):
        """Finds and processes all track JSON files."""
        self.log_manager.log("important", "=" * 40)
        self.log_manager.log("important", "🚀 Starting MixTracks Processing")
        self.log_manager.log("important", f"Project Root: {self.project_root}")
        self.log_manager.log("important", f"Searching Folders: {self.look_folders}")
        if self.mix_override:
             self.log_manager.log("important", f"Mix Override Applied: {self.mix_override}")
        self.log_manager.log("important", "=" * 40)

        track_json_files = self._find_track_json_files()

        if not track_json_files:
            self.log_manager.log("important", "⏹️ No track JSON files found in the specified folders.")
            return

        self.log_manager.log("important", f"ℹ️ Found {len(track_json_files)} potential track JSON files to process.")

        success_count = 0
        error_count = 0
        skipped_explicitly_count = 0

        for json_file in track_json_files:
            # Call process_track for each file and handle its return value
            result = self.process_track(json_file)
            if result is True:
                success_count += 1
            elif result == "ignored":
                skipped_explicitly_count += 1
            else: # result is False (an error occurred during processing)
                error_count += 1

        self.log_manager.log("important", "=" * 40)
        self.log_manager.log("important", "🏁 Processing Complete")
        self.log_manager.log("important", f"📊 Summary:")
        self.log_manager.log("important", f"    ✅ Successful Mixes: {success_count}")
        self.log_manager.log("important", f"    ⏭️ Skipped (ignore flags): {skipped_explicitly_count}")
        self.log_manager.log("important", f"    ❌ Errors/Failed Mixes: {error_count}")
        self.log_manager.log("important", "=" * 40)
