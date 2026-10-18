import os
import shutil
import subprocess
import importlib.util

from Core.ConfigManager import ConfigManager
from Core.LogManager import LogManager


# ============================================================
# CONSTANTS
# ============================================================

PLUGIN_NAME = "layer_export"

AUTO_ENV_FLAG = "KRITA_LAYER_EXPORT_AUTO"
OUTPUT_ENV_FLAG = "KRITA_LAYER_EXPORT_OUTPUT"
OBJECTS_ENV_FLAG = "KRITA_LAYER_EXPORT_OBJECTS"
LOG_DIR_ENV_FLAG = "KRITA_LAYER_EXPORT_LOG_DIR"

SCRIPTUTILS_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

PLUGIN_SOURCE_DIR = os.path.join(
    SCRIPTUTILS_ROOT,
    "ScriptUtils",
    "Core",
    "KritaExport",
    "KritaExportPlugin"
)

APPDATA_KRITA_DIR = os.path.join(
    os.environ.get("APPDATA", ""),
    "krita"
)

INSTALLED_PYKRITA_DIR = os.path.join(APPDATA_KRITA_DIR, "pykrita")
INSTALLED_PLUGIN_DIR = os.path.join(INSTALLED_PYKRITA_DIR, PLUGIN_NAME)


# ============================================================
# VERSION UTILITIES
# ============================================================

def read_plugin_version(version_file_path):
    if not os.path.exists(version_file_path):
        return None

    spec = importlib.util.spec_from_file_location("version", version_file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return getattr(module, "PLUGIN_VERSION", None)


def is_version_newer(source_version, installed_version):
    if not installed_version:
        return True

    def parse(v):
        return tuple(int(x) for x in v.split("."))

    return parse(source_version) > parse(installed_version)


# ============================================================
# INSTALL / UPDATE PLUGIN
# ============================================================

def ensure_plugin_installed(force_update=False):
    config = ConfigManager().load_config()
    log = LogManager(config.get("log_level", "normal"))

    source_version_file = os.path.join(PLUGIN_SOURCE_DIR, "version.py")
    installed_version_file = os.path.join(INSTALLED_PLUGIN_DIR, "version.py")

    source_version = read_plugin_version(source_version_file)
    installed_version = read_plugin_version(installed_version_file)

    needs_update = (
        force_update
        or not os.path.exists(INSTALLED_PLUGIN_DIR)
        or is_version_newer(source_version, installed_version)
    )

    if not needs_update:
        log.log("verbose", "KritaExport plugin is up to date.")
        return

    log.log("important", "Updating KritaExport plugin...")

    os.makedirs(INSTALLED_PYKRITA_DIR, exist_ok=True)

    # Remove old plugin folder
    if os.path.exists(INSTALLED_PLUGIN_DIR):
        shutil.rmtree(INSTALLED_PLUGIN_DIR)

    # Copy plugin folder (without desktop file)
    shutil.copytree(
        PLUGIN_SOURCE_DIR,
        INSTALLED_PLUGIN_DIR,
        ignore=shutil.ignore_patterns("*.desktop")
    )

    # Copy desktop file separately
    desktop_source = os.path.join(PLUGIN_SOURCE_DIR, "layer_export.desktop")
    desktop_target = os.path.join(INSTALLED_PYKRITA_DIR, "layer_export.desktop")

    shutil.copy2(desktop_source, desktop_target)

    log.log("important", f"KritaExport plugin installed:")
    log.log("important", f"  Plugin dir: {INSTALLED_PLUGIN_DIR}")
    log.log("important", f"  Desktop file: {desktop_target}")
    log.log("important", f"  Version: {source_version}")


# ============================================================
# MAIN EXPORT ENTRY
# ============================================================

def run_krita_export(
    kra_file,
    output_directory,
    objects=None,
    force_plugin_update=False
):
    config = ConfigManager().load_config()
    log = LogManager(config.get("log_level", "normal"))

    ensure_plugin_installed(force_update=force_plugin_update)

    krita_executable = config.get("krita_executable")

    if not krita_executable or not os.path.exists(krita_executable):
        log.log("important", "❌ Krita executable not found in config.")
        return False

    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )

    kra_file_abs = os.path.abspath(os.path.join(project_root, kra_file))
    output_dir_abs = os.path.abspath(os.path.join(project_root, output_directory))

    if not os.path.exists(kra_file_abs):
        log.log("important", f"❌ .kra file not found: {kra_file_abs}")
        return False

    os.makedirs(output_dir_abs, exist_ok=True)

    # Log directory = directory of calling script
    log_dir = os.getcwd()
    krita_log_file = os.path.join(log_dir, "krita-export.log")

    if os.path.exists(krita_log_file):
        os.remove(krita_log_file)

    env = os.environ.copy()
    env[AUTO_ENV_FLAG] = "1"
    env[OUTPUT_ENV_FLAG] = output_dir_abs
    env[LOG_DIR_ENV_FLAG] = log_dir

    if objects:
        env[OBJECTS_ENV_FLAG] = ",".join(objects)

    command = [
        krita_executable,
        "--nosplash",
        kra_file_abs
    ]

    log.log("normal", "🎨 Running Krita export:")
    log.log("verbose", " ".join(command))

    try:
        subprocess.run(command, check=True, env=env)
    except subprocess.CalledProcessError as e:
        log.log("important", f"❌ Krita process failed: {e}")
        return False

    # --------------------------------------------------------
    # Read Krita log
    # --------------------------------------------------------

    if os.path.exists(krita_log_file):
        log.log("normal", "📄 Krita plugin log:")
        with open(krita_log_file, "r", encoding="utf-8") as f:
            for line in f:
                log.log("normal", line.strip())
        return True
    else:
        log.log("important", "⚠ No Krita log produced.")
        return False