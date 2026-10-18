import os
import sys
import time
import zipfile
from datetime import datetime
from fnmatch import fnmatch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Shared")))

from base_script import BaseScript
from context import ParamGroup
from param import Param
from domain_utils import find_project_domain


DEFAULTS = {
    "log_level": 20,
    "log_file": None,

    "root": "",
    "folders": "",
    "destination_path": "Backups/project_backup_{DATE}.zip",
    "excludes": "*.tmp;*.log;Library/*;__pycache__/*",
}


class BackupScript(BaseScript):

    def define_groups(self):
        return [
            ParamGroup("Backup", [
                Param(
                    "root",
                    str,
                    DEFAULTS["root"],
                    label="Project root (override)",
                    description="Optional. Overrides the resolved root all other paths are relative to. "
                                 "Blank = discovered .uscript project root, else the current working directory."
                ),
                Param(
                    "folders",
                    str,
                    DEFAULTS["folders"],
                    label="Folders to back up",
                    description="Folders to include, relative to the resolved root (semicolon-separated)"
                ),
                Param(
                    "destination_path",
                    str,
                    DEFAULTS["destination_path"],
                    label="Destination zip",
                    description="Output .zip path, relative to the resolved root. Supports a {DATE} placeholder (YYYY-MM-DD)."
                ),
                Param(
                    "excludes",
                    str,
                    DEFAULTS["excludes"],
                    label="Exclude patterns",
                    description="Glob patterns excluded from the archive, matched against each file's path "
                                 "relative to the resolved root (semicolon-separated)"
                ),
            ]),
        ]

    def get_defaults(self):
        return DEFAULTS

    def preview(self, ctx):
        return f"Backup -> {ctx['destination_path']}"

    def _resolve_root(self, ctx):
        override = (ctx.get("root") or "").strip()
        if override:
            return os.path.abspath(override)

        extra = getattr(self.context, "extra", {})
        start = extra.get("cwd") or extra.get("selected") or os.getcwd()
        info = find_project_domain(str(start))
        return info.get("root_path") or os.getcwd()

    def _get_next_filename(self, filename):
        base, ext = os.path.splitext(filename)
        counter = 2
        new_filename = f"{base} ({counter}){ext}"
        while os.path.exists(new_filename):
            counter += 1
            new_filename = f"{base} ({counter}){ext}"
        self.log_info(f"Existing backup found. New name: {new_filename}")
        return new_filename

    def run(self, ctx):
        root = self._resolve_root(ctx)
        self.log_debug(f"Resolved root: {root}")

        folders = [f.strip() for f in ctx["folders"].split(";") if f.strip()]
        if not folders:
            self.log_error("No folders specified")
            return

        excludes = [e.strip() for e in ctx["excludes"].split(";") if e.strip()]
        abs_folders = [os.path.join(root, f) for f in folders]

        for folder in abs_folders:
            if not os.path.exists(folder):
                self.log_warn(f"Folder not found: {folder}")

        current_date = datetime.now().strftime("%Y-%m-%d")
        dest_rel = ctx["destination_path"].replace("{DATE}", current_date)
        destination_zip = os.path.abspath(os.path.join(root, dest_rel))

        if os.path.exists(destination_zip):
            self.log_info(f"{destination_zip} already exists.")
            destination_zip = self._get_next_filename(destination_zip)

        os.makedirs(os.path.dirname(destination_zip), exist_ok=True)
        self.log_info(f"Creating archive: {destination_zip}")

        start_time = time.time()
        total_files = 0

        with zipfile.ZipFile(destination_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for folder in abs_folders:
                if not os.path.exists(folder):
                    continue

                for froot, _dirs, files in os.walk(folder):
                    for file in files:
                        full_path = os.path.join(froot, file)
                        rel_path = os.path.relpath(full_path, root)

                        if any(fnmatch(rel_path, pattern) for pattern in excludes):
                            self.log_debug(f"Excluded by pattern: {rel_path}")
                            continue

                        zipf.write(full_path, rel_path)
                        total_files += 1
                        self.log_debug(f"Added: {rel_path}")

        duration = time.time() - start_time
        self.log_info(f"Backup complete: {destination_zip}")
        self.log_info(f"Files added: {total_files}")
        self.log_info(f"Duration: {duration:.2f}s")


if __name__ == "__main__":
    BackupScript().execute()
