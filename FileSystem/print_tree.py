import sys
import os
import fnmatch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../Shared")))

from base_script import BaseScript
from context import ParamGroup
from param import Param


DEFAULTS = {
    "log_level": 20,
    "log_file": "Tree.log",

    "path": ".",
    "print_full_list": True,
    "print_files_content": False,

    "prefix_text_md": "",
    "content_patterns": "*.py;*.txt;*.md;*.cmd;*.bat;*.css;*.cs;*.asmref;*.asmdef",
    "content_ignore_patterns": "",
    "ignore_patterns": "__pycache__;*.pyc;.git",
}


class PrintTreeScript(BaseScript):

    def define_groups(self):
        return [
            ParamGroup("Basic", [
                Param(
                    "path",
                    str,
                    DEFAULTS["path"],
                    label="Root path",
                    description="Starting location for the script (file or directory)"
                ),
                Param(
                    "print_full_list",
                    bool,
                    DEFAULTS["print_full_list"],
                    label="Print full file list",
                    description="Print the full path of all discovered files"
                ),
                Param(
                    "print_files_content",
                    bool,
                    DEFAULTS["print_files_content"],
                    label="Print files content",
                    description="Print the isolated content of matched files after the list"
                ),
            ]),
            ParamGroup("Content", [
                Param(
                    "prefix_text_md",
                    str,
                    DEFAULTS["prefix_text_md"],
                    label="Prefix text MD file",
                    description="Markdown file (relative to active preset/config folder) to prepend raw to output",
                ),
                Param(
                    "content_patterns",
                    str,
                    DEFAULTS["content_patterns"],
                    label="Content include patterns",
                    description="File patterns for which content is printed (semicolon-separated)",
                ),
                Param(
                    "content_ignore_patterns",
                    str,
                    DEFAULTS["content_ignore_patterns"],
                    label="Content ignore patterns",
                    description="Patterns excluded from content printing",
                ),
                Param(
                    "ignore_patterns",
                    str,
                    DEFAULTS["ignore_patterns"],
                    label="Ignore patterns",
                    description="Files and folders skipped completely",
                ),
            ])
        ]

    def get_defaults(self):
        return DEFAULTS

    def preview(self, ctx):
        return f"Target: {os.path.abspath(ctx['path'])}"

    def run(self, ctx):
        extra = getattr(self.context, "extra", {})

        root = os.path.abspath(ctx["path"])

        if os.path.isfile(root):
            root = os.path.dirname(root)

        if not os.path.isdir(root):
            if "cwd" in extra:
                root = os.path.abspath(extra["cwd"])
                if os.path.isfile(root):
                    root = os.path.dirname(root)
            else:
                self.log_error(f"Not a directory: {root}")
                return

        # ---------------------------------------------------------
        # 1. Prepend Prefix Markdown Text (100% Raw)
        # ---------------------------------------------------------
        prefix_file = ctx.get("prefix_text_md")
        if prefix_file and prefix_file.strip():
            prefix_file = prefix_file.strip()

            config_dir = extra.get("config_dir")
            if not config_dir:
                config_dir = os.path.dirname(os.path.abspath(__file__))
                try:
                    from domain_utils import find_project_domain
                    start_path = extra.get("cwd") or ctx["path"]
                    _, project_dir = find_project_domain(start_path)
                    if project_dir and os.path.exists(project_dir):
                        config_dir = project_dir
                except ImportError:
                    pass

            prefix_path = os.path.join(config_dir, prefix_file)
            
            if os.path.isfile(prefix_path):
                try:
                    with open(prefix_path, "r", encoding="utf-8") as f:
                        for line in f:
                            self.log_info(line.rstrip()) # Dump raw content
                    self.log_info("")  # Blank line separator after raw prefix
                except Exception as e:
                    self.log_warn(f"Failed to read prefix file: {prefix_path} ({e})")
            else:
                self.log_warn(f"Prefix MD file '{prefix_file}' not found in: {config_dir}")

        # ---------------------------------------------------------
        # 2. Collect Files and Directories
        # ---------------------------------------------------------
        def parse_patterns(s):
            return [p.strip() for p in s.split(";") if p.strip()]

        content_patterns = parse_patterns(ctx["content_patterns"])
        content_ignore = parse_patterns(ctx["content_ignore_patterns"])
        ignore_patterns = parse_patterns(ctx["ignore_patterns"])

        def match_any(name, patterns):
            return any(fnmatch.fnmatch(name, p) for p in patterns)

        collected_files = []

        def collect_entries(path):
            try:
                entries = sorted(os.listdir(path))
            except Exception as e:
                self.log_error(f"Failed to access: {path} ({e})")
                return

            for e in entries:
                if match_any(e, ignore_patterns):
                    continue

                full_path = os.path.join(path, e)

                if os.path.isdir(full_path):
                    collect_entries(full_path)
                else:
                    collected_files.append(full_path)

        collect_entries(root)

        # ---------------------------------------------------------
        # 3. Print Full File List (if enabled)
        # ---------------------------------------------------------
        if ctx["print_full_list"]:
            self.log_info(f"### FILE LIST ({len(collected_files)} files discovered):")
            for file_path in collected_files:
                self.log_info(file_path)
            self.log_info("")  # Blank line separator

        # ---------------------------------------------------------
        # 4. Print Files Content (if enabled)
        # ---------------------------------------------------------
        if ctx["print_files_content"]:
            self.log_info("### FILES CONTENT:")
            
            for full_path in collected_files:
                filename = os.path.basename(full_path)

                # Filter by content include/ignore patterns
                if match_any(filename, content_patterns) and not match_any(filename, content_ignore):
                    
                    # XML / LLM-Friendly Isolation Strings
                    self.log_info(f'<file path="{full_path}">')
                    try:
                        with open(full_path, "r", encoding="utf-8") as file:
                            for line in file:
                                self.log_info(line.rstrip())
                    except Exception as e:
                        self.log_warn(f"Failed to read file: {full_path} ({e})")
                    self.log_info("</file>")
                    self.log_info("") # Spacing between isolated files


if __name__ == "__main__":
    PrintTreeScript().execute()