import os
import sys
from pathlib import Path

# --- match Shared import pattern ---
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../Shared")
))

from base_script import BaseScript
from context import ParamGroup
from param import Param
from domain_utils import find_project_domain
from export_impl import KritaExporter

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

        exporter = KritaExporter(self, ctx, project_info)
        exporter.ensure_plugin_installed()

        for kra_file in kra_files:
            exporter.process_file(kra_file)

        self.log_info("Batch export complete.")

if __name__ == "__main__":
    KritaExportScript().execute()