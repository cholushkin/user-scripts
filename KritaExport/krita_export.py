import os
import sys
import shutil
import subprocess
import importlib.util
import json
from pathlib import Path

# --- match Shared import pattern ---
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../Shared")
))

from base_script import BaseScript
from context import ParamGroup
from param import Param
from domain_utils import find_project_domain

# ============================================================
# CONSTANTS
# ============================================================
PLUGIN_NAME = "layer_export"

AUTO_ENV_FLAG = "KRITA_LAYER_EXPORT_AUTO"
OUTPUT_ENV_FLAG = "KRITA_LAYER_EXPORT_OUTPUT"
OBJECTS_ENV_FLAG = "KRITA_LAYER_EXPORT_OBJECTS"
LOG_DIR_ENV_FLAG = "KRITA_LAYER_EXPORT_LOG_DIR"

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_SOURCE_DIR = os.path.join(SCRIPT_DIR, "KritaExportPlugin")

APPDATA_KRITA_DIR = os.path.join(os.environ.get("APPDATA", ""), "krita")
INSTALLED_PYKRITA_DIR = os.path.join(APPDATA_KRITA_DIR, "pykrita")
INSTALLED_PLUGIN_DIR = os.path.join(INSTALLED_PYKRITA_DIR, PLUGIN_NAME)

# ============================================================
# SCRIPT
# ============================================================
class KritaExportScript(BaseScript):

    def define_groups(self):
        return [
            ParamGroup("Export Settings", [
                Param("krita_exe", str, default=r"C:\Program Files\Krita (x64)\bin\krita.exe", label="Krita Executable"),
                Param("output_dir", str, default="", label="Output Directory Override (Optional)"),
                Param("objects", str, default="", label="Objects Filter (comma-separated)"),
                Param("force_update", bool, default=False, label="Force Plugin Update")
            ])
        ]

    def run(self, ctx):
        self._ensure_plugin_installed(ctx["force_update"])

        extra = getattr(self.context, "extra", {})
        
        # 1. Resolve base directory from cwd context 
        raw_cwd = extra.get("cwd", "")
        base_dir = ""
        if raw_cwd:
            base_dir = os.path.dirname(raw_cwd) if os.path.isfile(raw_cwd) else raw_cwd

        paths = []

        # 2. Double Commander selection (PRIMARY)
        selected_file = extra.get("selected")
        if selected_file and Path(selected_file).exists():
            with open(selected_file, "r", encoding="utf-8") as f:
                for line in f:
                    p = line.strip()
                    if p:
                        if not os.path.isabs(p) and base_dir:
                            p = os.path.join(base_dir, p)
                        paths.append(p)

        # 3. Fallback (Current Working Directory/File)
        if not paths and raw_cwd:
            paths = [raw_cwd]

        # Filter strictly for .kra files
        kra_files = [p for p in paths if p.lower().endswith('.kra')]

        if not kra_files:
            self.log_warn("No .kra files selected or found in context.")
            return

        # 4. Resolve Domain Config (Ensures it works even in headless executions)
        start_path_for_domain = kra_files[0] if kra_files else raw_cwd
        project_info = find_project_domain(start_path_for_domain)

        for kra_file in kra_files:
            self._process_single_file(kra_file, ctx, project_info)

        self.log_info("Batch export complete.")

    def _process_single_file(self, kra_file, ctx, project_info):
        kra_file = os.path.abspath(kra_file)
        self.log_info(f"--- Processing: {os.path.basename(kra_file)} ---")
        
        if not os.path.exists(kra_file):
            self.log_error(f"File not found: {kra_file}")
            return

        # 1. Parse JSON mapping
        base_name = os.path.splitext(kra_file)[0]
        json_path = f"{base_name}.json"
        
        json_objects = []
        subfolder = ""

        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    per_file_settings = json.load(f)
                
                export_params = per_file_settings.get("export_parameters", {})
                objects = export_params.get("objects", [])
                
                if objects:
                    subfolder = objects[0].get("subfolder", "")
                    json_objects = [obj.get("layer") for obj in objects if "layer" in obj]
                            
                self.log_info(f"Loaded JSON config (Found {len(json_objects)} target objects, Subfolder: '{subfolder}')")
            except Exception as e:
                self.log_error(f"Failed to read JSON config at {json_path}: {e}")

        # 2. Determine Output Directory
        out_dir = ctx.get("output_dir", "").strip()
        
        if out_dir:
            # Explicit UI override wins
            final_output_dir = Path(out_dir)
        elif project_info.get("root_path") and project_info.get("asset_folder"):
            # Intelligent project resolution
            final_output_dir = Path(project_info["root_path"]) / project_info["asset_folder"] / subfolder
        else:
            # Standalone mode fallback (e.g. running outside of a known repository)
            self.log_info("Running standalone (No project config found). Exporting relative to source file.")
            final_output_dir = Path(kra_file).parent / subfolder
            
        os.makedirs(final_output_dir, exist_ok=True)
        self.log_info(f"Target Output Directory: {final_output_dir}")

        # 3. Setup Environment Variables
        log_dir = os.getcwd()
        krita_log_file = os.path.join(log_dir, "krita-export.log")

        if os.path.exists(krita_log_file):
            os.remove(krita_log_file)

        env = os.environ.copy()
        env[AUTO_ENV_FLAG] = "1"
        env[OUTPUT_ENV_FLAG] = str(final_output_dir.resolve())
        env[LOG_DIR_ENV_FLAG] = log_dir

        # UI Filter overrides JSON Filter
        objects_filter = ctx.get("objects", "").strip()
        if not objects_filter and json_objects:
            objects_filter = ",".join(json_objects)
            
        if objects_filter:
            env[OBJECTS_ENV_FLAG] = objects_filter

        # 4. Execute Subprocess
        command = [
            ctx["krita_exe"],
            "--nosplash",
            kra_file
        ]

        self.log_info("Running Krita headless...")

        try:
            subprocess.run(command, check=True, env=env)
        except subprocess.CalledProcessError as e:
            self.log_error(f"Krita process failed: {e}")
            return

        self._pipe_krita_logs(krita_log_file)

    def _ensure_plugin_installed(self, force_update):
        source_version_file = os.path.join(PLUGIN_SOURCE_DIR, "version.py")
        installed_version_file = os.path.join(INSTALLED_PLUGIN_DIR, "version.py")

        source_version = self._read_plugin_version(source_version_file)
        installed_version = self._read_plugin_version(installed_version_file)

        needs_update = (
            force_update
            or not os.path.exists(INSTALLED_PLUGIN_DIR)
            or self._is_version_newer(source_version, installed_version)
        )

        self._enable_plugin_in_kritarc()

        if not needs_update:
            self.log_debug("KritaExport plugin is up to date.")
            return

        self.log_info("Updating KritaExport plugin in Krita AppData...")

        os.makedirs(INSTALLED_PYKRITA_DIR, exist_ok=True)

        if os.path.exists(INSTALLED_PLUGIN_DIR):
            shutil.rmtree(INSTALLED_PLUGIN_DIR)

        shutil.copytree(
            PLUGIN_SOURCE_DIR,
            INSTALLED_PLUGIN_DIR,
            ignore=shutil.ignore_patterns("*.desktop")
        )

        desktop_source = os.path.join(PLUGIN_SOURCE_DIR, "layer_export.desktop")
        desktop_target = os.path.join(INSTALLED_PYKRITA_DIR, "layer_export.desktop")
        shutil.copy2(desktop_source, desktop_target)

        self.log_info(f"Plugin installed to: {INSTALLED_PLUGIN_DIR}")

    def _enable_plugin_in_kritarc(self):
        kritarc_path = os.path.join(APPDATA_KRITA_DIR, "kritarc")
        if not os.path.exists(kritarc_path):
            return

        try:
            with open(kritarc_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            out_lines = []
            in_section = False
            found_key = False
            section_found = False

            for line in lines:
                if line.strip() == "[pythonPlugins]":
                    in_section = True
                    section_found = True
                    out_lines.append(line)
                    continue
                elif line.strip().startswith("["):
                    if in_section and not found_key:
                        out_lines.append("layer_export=true\n")
                        found_key = True
                    in_section = False

                if in_section and line.startswith("layer_export="):
                    out_lines.append("layer_export=true\n")
                    found_key = True
                else:
                    out_lines.append(line)

            if not section_found:
                out_lines.append("\n[pythonPlugins]\nlayer_export=true\n")
            elif in_section and not found_key:
                out_lines.append("layer_export=true\n")

            with open(kritarc_path, 'w', encoding='utf-8') as f:
                f.writelines(out_lines)
                
        except Exception as e:
            self.log_warn(f"Failed to configure kritarc: {e}")

    def _pipe_krita_logs(self, log_file):
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    self.log_info(f"[Krita] {line.strip()}")
        else:
            self.log_warn("No Krita log file produced.")

    def _read_plugin_version(self, version_file_path):
        if not os.path.exists(version_file_path):
            return None
        spec = importlib.util.spec_from_file_location("version", version_file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, "PLUGIN_VERSION", None)

    def _is_version_newer(self, source_version, installed_version):
        if not installed_version:
            return True
        def parse(v): return tuple(int(x) for x in v.split("."))
        return parse(source_version) > parse(installed_version)

if __name__ == "__main__":
    KritaExportScript().execute()