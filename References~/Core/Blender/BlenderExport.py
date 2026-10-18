import os
import subprocess
import sys

# Add Core to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from Core.ConfigManager import ConfigManager
from Core.LogManager import LogManager

def run_blender_export(blend_file, export_directory, unity_axis_conversion, objects_to_export):
    config = ConfigManager().load_config()
    log = LogManager(config.get("log_level", "normal"))
    blender_executable = config.get("blender_executable")
    unity_project_root = config.get("unity_project_root")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    script_path = os.path.join(project_root, "ScriptUtils", "Core", "Blender", "ExportFbxObject.py")
    blend_file_abs = os.path.abspath(os.path.join(project_root, blend_file))
    export_dir_abs = os.path.abspath(os.path.join(project_root, unity_project_root, export_directory))

    os.makedirs(export_dir_abs, exist_ok=True)

    command = [
        blender_executable,
        "--background",
        "--python", script_path,
        "--",
        blend_file_abs,
        export_dir_abs,
        str(unity_axis_conversion).lower()
    ] + objects_to_export

    log.log("normal", f"🚀 Running Blender command:\n{' '.join(command)}")
    log.log("verbose", f"Blender executable : {blender_executable}\n")

    try:
        subprocess.run(command, check=True)
        log.log("important", "✅ Blender export completed successfully.")
    except subprocess.CalledProcessError as e:
        log.log("important", f"❌ Blender process failed: {e}")
