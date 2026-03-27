import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../Shared")))
from base_script import BaseScript
from context import ParamGroup
from param import Param


# -------------------------
# DEFAULTS (USER-EDITABLE)
# -------------------------

DEFAULTS = {
    # logging
    "log_level": 20,         # 10=DEBUG, 20=INFO, 30=WARN, 40=ERROR
    "log_file": "Tree.log",        # e.g. "tree.log"

    # script-specific
    "path": ".",
    "dirs_only": False,
}


class PrintTreeScript(BaseScript):

    # -------------------------
    # PARAMS
    # -------------------------

    def define_groups(self):
        return [
            ParamGroup("Basic", [
                Param("path", str, DEFAULTS["path"], label="Root path"),
                Param("dirs_only", bool, DEFAULTS["dirs_only"], label="Directories only"),
            ])
        ]

    # -------------------------
    # BASE DEFAULT OVERRIDE
    # -------------------------

    def get_defaults(self):
        return DEFAULTS

    # -------------------------
    # PREVIEW
    # -------------------------

    def preview(self, ctx):
        return f"Tree of: {os.path.abspath(ctx['path'])}"

    # -------------------------
    # LOGIC
    # -------------------------
    def run(self, ctx):
        extra = getattr(self.context, "extra", {})

        root = ctx["path"]
        root = os.path.abspath(root)

        # if it's a file → take parent directory
        if os.path.isfile(root):
            root = os.path.dirname(root)

        # if still not valid → fallback to cwd (future-safe)
        if not os.path.isdir(root):
            if "cwd" in extra:
                root = extra["cwd"]
                root = os.path.abspath(root)

                if os.path.isfile(root):
                    root = os.path.dirname(root)
            else:
                self.log_error(f"Not a directory: {root}")
                return
        dirs_only = ctx["dirs_only"]

        # print root
        self.log_info(root)

        def walk(path, level):
            try:
                entries = os.listdir(path)
            except Exception as e:
                self.log_error(f"Failed to access: {path} ({e})")
                return

            entries.sort()

            indent = "    " * (level + 1)

            # separate dirs and files
            dirs = []
            files = []

            for e in entries:
                full = os.path.join(path, e)
                if os.path.isdir(full):
                    dirs.append(e)
                else:
                    files.append(e)

            # process directories FIRST (depth-first)
            for d in dirs:
                self.log_info(f"{indent}{d}")
                walk(os.path.join(path, d), level + 1)

            # then files
            if not dirs_only:
                for f in files:
                    self.log_info(f"{indent}{f}")

        walk(root, 0)


# -------------------------
# ENTRY
# -------------------------

if __name__ == "__main__":
    PrintTreeScript().execute()