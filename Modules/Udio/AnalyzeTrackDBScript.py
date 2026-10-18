import os
import sys
import json
import time
import hashlib

from mutagen.mp3 import MP3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Shared")))

from base_script import BaseScript
from context import ParamGroup
from param import Param


DEFAULTS = {
    "log_level": 20,
    "log_file": None,

    "look_folders": "",
    "estimate_bitrates": "128k;192k;256k;320k",
}


class AnalyzeTrackDBScript(BaseScript):
    """
    Scans look_folders for MP3 files with matching JSON metadata, reporting
    duration/size totals, estimated size at other bitrates, and duplicate
    files (by MD5 and by filename).
    """

    def define_groups(self):
        return [
            ParamGroup("Analyze", [
                Param(
                    "look_folders",
                    str,
                    DEFAULTS["look_folders"],
                    description="Folders to scan for MP3/JSON track pairs (relative to --cwd, or absolute; semicolon-separated)"
                ),
                Param(
                    "estimate_bitrates",
                    str,
                    DEFAULTS["estimate_bitrates"],
                    description="Bitrates to estimate total library size at (semicolon-separated, e.g. '128k;192k')"
                ),
            ]),
        ]

    def get_defaults(self):
        return DEFAULTS

    def preview(self, ctx):
        return f"Analyze track DB in [{ctx['look_folders']}]"

    def _resolve(self, base, path):
        return path if os.path.isabs(path) else os.path.join(base, path)

    def _get_mp3_duration(self, file_path):
        try:
            audio = MP3(file_path)
            duration = int(audio.info.length)
            minutes, seconds = duration // 60, duration % 60
            return duration, f"{minutes}:{seconds:02d}"
        except Exception:
            return 0, "Unknown"

    def _read_track_metadata(self, json_file):
        metadata = {"energy": None, "mood": None, "pop": None, "stars": None, "export": False}
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "tags" in data:
                metadata.update({
                    "energy": data["tags"].get("energy"),
                    "mood": data["tags"].get("mood"),
                    "pop": data["tags"].get("pop"),
                    "stars": data["tags"].get("stars"),
                })
            if "export_parameters" in data:
                metadata["export"] = data["export_parameters"].get("export", False)
        except Exception as e:
            self.log_warn(f"Error reading {json_file}: {e}")
        return metadata

    def _estimate_size(self, total_duration, bitrates):
        sizes = {}
        for bitrate in bitrates:
            try:
                kbps = int(bitrate.replace("k", ""))
            except ValueError:
                self.log_warn(f"Invalid bitrate '{bitrate}', skipping.")
                continue
            sizes[bitrate] = (total_duration * kbps / 8) / 1024
        return sizes

    def run(self, ctx):
        extra = getattr(self.context, "extra", {})
        base = extra.get("cwd") or os.getcwd()

        look_folders = [f.strip() for f in ctx["look_folders"].split(";") if f.strip()]
        if not look_folders:
            self.log_error("look_folders is required")
            return
        abs_folders = [self._resolve(base, f) for f in look_folders]

        estimate_bitrates = [b.strip() for b in ctx["estimate_bitrates"].split(";") if b.strip()]

        start_time = time.time()
        total_size = 0
        total_duration = 0
        mp3_count = 0
        md5_hashes = {}
        name_duplicates = {}

        self.log_info("Searching for MP3 files with corresponding JSON metadata...")

        for folder in abs_folders:
            if not os.path.isdir(folder):
                self.log_warn(f"Folder not found: {folder}")
                continue

            self.log_debug(f"Searching in: {folder}")
            for root, _dirs, files in os.walk(folder):
                for file in files:
                    if not file.lower().endswith(".mp3"):
                        continue

                    file_path = os.path.join(root, file)
                    json_file = os.path.splitext(file_path)[0] + ".json"

                    if not os.path.exists(json_file):
                        self.log_warn(f"JSON metadata not found for {file}")
                        continue

                    metadata = self._read_track_metadata(json_file)
                    duration_seconds, duration_str = self._get_mp3_duration(file_path)

                    with open(file_path, "rb") as f:
                        md5 = hashlib.md5(f.read()).hexdigest()
                    md5_hashes.setdefault(md5, []).append(file_path)
                    name_duplicates.setdefault(file, []).append(file_path)

                    marker = "+" if metadata["export"] else "-"
                    line = f"{marker} {file} [{duration_str}]"
                    if metadata["energy"] is not None:
                        line += f" energy={metadata['energy']:.1f}"
                    if metadata["mood"] is not None:
                        line += f" mood={metadata['mood']:.1f}"
                    if metadata["pop"] is not None:
                        line += f" pop={metadata['pop']:.1f}"
                    if metadata["stars"] is not None:
                        line += f" stars={int(metadata['stars'])}"
                    self.log_info(line)

                    total_size += os.path.getsize(file_path)
                    total_duration += duration_seconds
                    mp3_count += 1

        self.log_info("")
        self.log_info("Summary:")
        self.log_info(f"Total MP3 files analyzed (with JSON metadata): {mp3_count}")
        self.log_info(f"Total space occupied: {total_size / (1024 * 1024):.2f} MB")
        h, m, s = total_duration // 3600, (total_duration % 3600) // 60, total_duration % 60
        self.log_info(f"Total duration: {h:02d}:{m:02d}:{s:02d}")

        self.log_info("")
        self.log_info("Estimated total size at different bitrates:")
        for bitrate, size in self._estimate_size(total_duration, estimate_bitrates).items():
            self.log_info(f"  {bitrate}: {size:.2f} MB")

        md5_dupes = [v for v in md5_hashes.values() if len(v) > 1]
        name_dupes = [v for v in name_duplicates.values() if len(v) > 1]

        if md5_dupes or name_dupes:
            self.log_info("")
            self.log_info("Duplicate files found:")
            count = 1
            for group in md5_dupes:
                for i in range(len(group) - 1):
                    self.log_info(f'{count}. "{group[i]}" and "{group[i + 1]}" (same MD5)')
                    count += 1
            for group in name_dupes:
                for i in range(len(group) - 1):
                    self.log_info(f'{count}. "{group[i]}" and "{group[i + 1]}" (same name)')
                    count += 1

        elapsed = time.time() - start_time
        self.log_info("")
        self.log_info(f"Execution time: {elapsed:.2f}s")
        self.log_info("Finished analyzing files.")


if __name__ == "__main__":
    AnalyzeTrackDBScript().execute()
