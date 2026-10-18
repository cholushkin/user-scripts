import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Shared")))

from base_script import BaseScript
from context import ParamGroup
from param import Param
from domain_utils import find_project_domain


DEFAULTS = {
    "log_level": 20,
    "log_file": None,

    "blender_exe": r"C:\Program Files\Blender Foundation\Blender\blender.exe",
    "blend_file": "",
    "export_dir": "",
    "unity_axis_conversion": True,
    "objects": "",
}


class BlenderExportScript(BaseScript):

    def define_groups(self):
        return [
            ParamGroup("Export Settings", [
                Param("blender_exe", str, DEFAULTS["blender_exe"], label="Blender Executable"),
                Param(
                    "blend_file",
                    str,
                    DEFAULTS["blend_file"],
                    label=".blend file",
                    description="Path to the .blend file to export from. Blank = use the Double Commander "
                                "selection/cwd if it points at a .blend file."
                ),
                Param(
                    "export_dir",
                    str,
                    DEFAULTS["export_dir"],
                    label="Export Directory Override (Optional)",
                    description="Blank = resolved via the discovered .uscript project's asset folder, "
                                "else the current working directory."
                ),
                Param(
                    "unity_axis_conversion",
                    bool,
                    DEFAULTS["unity_axis_conversion"],
                    label="Unity axis conversion",
                    description="On: forward=-Z, up=Y (matches Unity). Off: forward=Y, up=Z (Blender default)."
                ),
                Param(
                    "objects",
                    str,
                    DEFAULTS["objects"],
                    label="Objects to export",
                    description="Object names to export, each with its full child hierarchy (semicolon-separated)"
                ),
            ]),
        ]

    def get_defaults(self):
        return DEFAULTS

    def preview(self, ctx):
        return f"Export [{ctx.get('objects') or '?'}] -> {ctx.get('export_dir') or '(auto)'}"

    def _resolve_blend_file(self, ctx, extra):
        blend_file = (ctx.get("blend_file") or "").strip()
        if blend_file:
            return blend_file

        selected_file = extra.get("selected")
        if selected_file and Path(selected_file).exists():
            with open(selected_file, "r", encoding="utf-8") as f:
                for line in f:
                    p = line.strip()
                    if p.lower().endswith(".blend"):
                        return p

        cwd = extra.get("cwd")
        if cwd and str(cwd).lower().endswith(".blend"):
            return str(cwd)

        return ""

    def _resolve_export_dir(self, ctx, extra, blend_file_abs):
        override = (ctx.get("export_dir") or "").strip()
        if override:
            return os.path.abspath(override)

        start = extra.get("cwd") or blend_file_abs
        info = find_project_domain(str(start))
        asset_folder = info.get("asset_folder")
        if asset_folder:
            return os.path.abspath(asset_folder)

        return os.path.abspath(extra.get("cwd") or os.path.dirname(blend_file_abs))

    def run(self, ctx):
        extra = getattr(self.context, "extra", {})

        blend_file = self._resolve_blend_file(ctx, extra)
        if not blend_file or not os.path.exists(blend_file):
            self.log_error("No .blend file provided (set 'blend_file' or select one in the file manager).")
            return
        blend_file_abs = os.path.abspath(blend_file)

        objects = [o.strip() for o in (ctx.get("objects") or "").split(";") if o.strip()]
        if not objects:
            self.log_error("No objects specified to export.")
            return

        export_dir = self._resolve_export_dir(ctx, extra, blend_file_abs)
        os.makedirs(export_dir, exist_ok=True)

        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ExportFbxObject.py")

        command = [
            ctx["blender_exe"],
            "--background",
            "--python", script_path,
            "--",
            blend_file_abs,
            export_dir,
            str(bool(ctx["unity_axis_conversion"])).lower(),
        ] + objects

        self.log_info(f"Running Blender: {' '.join(command)}")

        try:
            subprocess.run(command, check=True)
            self.log_info("Blender export completed successfully.")
        except FileNotFoundError:
            self.log_error(f"Blender executable not found: {ctx['blender_exe']}")
        except subprocess.CalledProcessError as e:
            self.log_error(f"Blender process failed: {e}")


if __name__ == "__main__":
    BlenderExportScript().execute()
