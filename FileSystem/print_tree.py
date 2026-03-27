import sys
import os
import fnmatch

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
    "log_file": "Tree.log",  # e.g. "tree.log"

    # script-specific
    "path": ".",
    "dirs_only": False,

    # content control
    "content_patterns": "*.py;*.txt;*.md;*.cmd;*.bat",
    "content_ignore_patterns": "",
    "ignore_patterns": "__pycache__;*.pyc;.git",
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
            ]),
            ParamGroup("Content", [
                Param("content_patterns", str, DEFAULTS["content_patterns"]),
                Param("content_ignore_patterns", str, DEFAULTS["content_ignore_patterns"]),
                Param("ignore_patterns", str, DEFAULTS["ignore_patterns"]),
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

        # fallback to cwd
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

        # -------------------------
        # PATTERN HELPERS
        # -------------------------

        def parse_patterns(s):
            return [p.strip() for p in s.split(";") if p.strip()]

        content_patterns = parse_patterns(ctx["content_patterns"])
        content_ignore = parse_patterns(ctx["content_ignore_patterns"])
        ignore_patterns = parse_patterns(ctx["ignore_patterns"])

        def match_any(name, patterns):
            return any(fnmatch.fnmatch(name, p) for p in patterns)

        # -------------------------
        # START OUTPUT
        # -------------------------

        self.log_info(root)

        def walk(path, level):
            try:
                entries = os.listdir(path)
            except Exception as e:
                self.log_error(f"Failed to access: {path} ({e})")
                return

            entries.sort()

            indent = "    " * (level + 1)

            dirs = []
            files = []

            for e in entries:
                if match_any(e, ignore_patterns):
                    continue

                full = os.path.join(path, e)

                if os.path.isdir(full):
                    dirs.append(e)
                else:
                    files.append(e)

            # -------------------------
            # DIRECTORIES (DFS)
            # -------------------------

            for d in dirs:
                self.log_info(f"{indent}{d}")
                walk(os.path.join(path, d), level + 1)

            # -------------------------
            # FILES
            # -------------------------

            if not dirs_only:
                for f in files:
                    self.log_info(f"{indent}{f}")

                    # -------------------------
                    # CONTENT PRINTING
                    # -------------------------

                    if match_any(f, content_patterns) and not match_any(f, content_ignore):
                        full_path = os.path.join(path, f)

                        # separator start
                        self.log_info(f"{indent}// --- Start File: {full_path} ---")

                        try:
                            with open(full_path, "r", encoding="utf-8") as file:
                                for line in file:
                                    line = line.rstrip()
                                    if line:
                                        self.log_info(f"{indent}    {line}")
                        except Exception as e:
                            self.log_warn(f"Failed to read file: {full_path} ({e})")

                        # separator end
                        self.log_info(f"{indent}// --- End File: {full_path} ---")

        walk(root, 0)


# -------------------------
# ENTRY
# -------------------------

if __name__ == "__main__":
    PrintTreeScript().execute()