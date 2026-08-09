import os
import shutil
import subprocess
import importlib.util
from pathlib import Path

# ============================================================
# CONSTANTS
# ============================================================
PLUGIN_NAME = "layer_export"

AUTO_ENV_FLAG = "KRITA_LAYER_EXPORT_AUTO"
JSON_ENV_FLAG = "KRITA_LAYER_EXPORT_JSON"
ROOT_ENV_FLAG = "KRITA_LAYER_EXPORT_ROOT"
ASSETS_ENV_FLAG = "KRITA_LAYER_EXPORT_ASSETS"
OUT_OVERRIDE_ENV_FLAG = "KRITA_LAYER_EXPORT_OUT_OVERRIDE"
OBJECTS_ENV_FLAG = "KRITA_LAYER_EXPORT_OBJECTS"
LOG_DIR_ENV_FLAG = "KRITA_LAYER_EXPORT_LOG_DIR"

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_SOURCE_DIR = os.path.join(SCRIPT_DIR, "KritaExportPlugin")

APPDATA_KRITA_DIR = os.path.join(os.environ.get("APPDATA", ""), "krita")
INSTALLED_PYKRITA_DIR = os.path.join(APPDATA_KRITA_DIR, "pykrita")
INSTALLED_PLUGIN_DIR = os.path.join(INSTALLED_PYKRITA_DIR, PLUGIN_NAME)

class KritaExporter:
    def __init__(self, script_instance, ctx, project_info):
        self.script = script_instance
        self.ctx = ctx
        self.project_info = project_info or {}
        
    def ensure_plugin_installed(self):
        force_update = self.ctx.get("force_update", False)
        self._ensure_plugin_installed(force_update)

    def process_file(self, kra_file):
        kra_file = os.path.abspath(kra_file)
        self.script.log_info(f"--- Processing: {os.path.basename(kra_file)} ---")
        
        if not os.path.exists(kra_file):
            self.script.log_error(f"File not found: {kra_file}")
            return

        base_name = os.path.splitext(kra_file)[0]
        json_path = f"{base_name}.json"
        
        log_dir = os.getcwd()
        krita_log_file = os.path.join(log_dir, "krita-export.log")

        if os.path.exists(krita_log_file):
            try: os.remove(krita_log_file)
            except OSError: pass

        # Inject Data to Krita Plugin Environment
        env = os.environ.copy()
        env[AUTO_ENV_FLAG] = "1"
        env[LOG_DIR_ENV_FLAG] = log_dir

        if os.path.exists(json_path):
            env[JSON_ENV_FLAG] = str(Path(json_path).resolve())
            self.script.log_info(f"Found JSON configuration: {json_path}")
        else:
            self.script.log_info("No JSON config found. Using default logic.")

        if self.project_info:
            env[ROOT_ENV_FLAG] = str(self.project_info.get("root_path", ""))
            env[ASSETS_ENV_FLAG] = str(self.project_info.get("asset_folder", ""))

        out_dir = self.ctx.get("output_dir", "").strip()
        if out_dir:
            env[OUT_OVERRIDE_ENV_FLAG] = str(Path(out_dir).resolve())

        objects_filter = self.ctx.get("objects", "").strip()
        if objects_filter:
            env[OBJECTS_ENV_FLAG] = objects_filter

        # Execute
        command = [self.ctx["krita_exe"], "--nosplash", kra_file]
        self.script.log_info("Running Krita headless...")

        try:
            subprocess.run(command, check=True, env=env)
        except subprocess.CalledProcessError as e:
            self.script.log_error(f"Krita process failed: {e}")
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
            self.script.log_debug("KritaExport plugin is up to date.")
            return

        self.script.log_info("Updating KritaExport plugin in Krita AppData...")
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
        self.script.log_info(f"Plugin installed to: {INSTALLED_PLUGIN_DIR}")

    def _enable_plugin_in_kritarc(self):
        kritarc_path = os.path.join(APPDATA_KRITA_DIR, "kritarc")
        if not os.path.exists(kritarc_path): return

        try:
            with open(kritarc_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            out_lines, in_section, found_key, section_found = [], False, False, False

            for line in lines:
                if line.strip() == "[pythonPlugins]":
                    in_section = section_found = True
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
            self.script.log_warn(f"Failed to configure kritarc: {e}")

    def _pipe_krita_logs(self, log_file):
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f: self.script.log_info(f"[Krita] {line.strip()}")
        else:
            self.script.log_warn("No Krita log file produced.")

    def _read_plugin_version(self, version_file_path):
        if not os.path.exists(version_file_path): return None
        spec = importlib.util.spec_from_file_location("version", version_file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, "PLUGIN_VERSION", None)

    def _is_version_newer(self, source_version, installed_version):
        if not installed_version: return True
        def parse(v): return tuple(int(x) for x in v.split("."))
        return parse(source_version) > parse(installed_version)