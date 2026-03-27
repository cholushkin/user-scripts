import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../Shared")))

from base_script import BaseScript
from context import ParamGroup
from param import Param


# -------------------------
# DEFAULTS (USER-EDITABLE)
# -------------------------
DEFAULTS = {
    # logging
    "log_level": 20,
    "log_file": None,

    # emoji behavior
    "group": "all",          # all, faces, symbols, transport, etc.
    "columns": 16,           # emojis per row
    "spacing": 1,            # spaces between emojis
    "max_count": 0,          # 0 = unlimited
    "show_codepoint": False, # print hex codes
}


# -------------------------
# EMOJI GROUPS
# -------------------------
EMOJI_GROUPS = {
    "faces": [(0x1F600, 0x1F64F)],
    "symbols": [(0x2600, 0x26FF), (0x2700, 0x27BF)],
    "transport": [(0x1F680, 0x1F6FF)],
    "shapes": [(0x1F780, 0x1F7FF)],
    "extended": [(0x1F900, 0x1F9FF), (0x1FA00, 0x1FAFF)],
    "all": [
        (0x1F600, 0x1F64F),
        (0x1F300, 0x1F5FF),
        (0x1F680, 0x1F6FF),
        (0x1F700, 0x1F77F),
        (0x1F780, 0x1F7FF),
        (0x1F800, 0x1F8FF),
        (0x1F900, 0x1F9FF),
        (0x1FA00, 0x1FAFF),
        (0x1FB00, 0x1FBFF),
        (0x2600, 0x26FF),
        (0x2700, 0x27BF),
    ],
}


# -------------------------
# SCRIPT
# -------------------------
class EmojiScript(BaseScript):

    # -------------------------
    # PARAMS
    # -------------------------
    def define_groups(self):
        return [
            ParamGroup("Display", [
                Param("group", str, DEFAULTS["group"], hints=list(EMOJI_GROUPS.keys())),
                Param("columns", int, DEFAULTS["columns"]),
                Param("spacing", int, DEFAULTS["spacing"]),
                Param("max_count", int, DEFAULTS["max_count"]),
                Param("show_codepoint", bool, DEFAULTS["show_codepoint"]),
            ])
        ]

    # -------------------------
    # DEFAULTS
    # -------------------------
    def get_defaults(self):
        return DEFAULTS

    # -------------------------
    # PREVIEW
    # -------------------------
    def preview(self, ctx):
        return f"Emoji grid ({ctx['group']})"

    # -------------------------
    # LOGIC
    # -------------------------
    def run(self, ctx):

        group_name = ctx["group"]
        columns = max(1, ctx["columns"])
        spacing = " " * max(0, ctx["spacing"])
        max_count = ctx["max_count"]
        show_code = ctx["show_codepoint"]

        if group_name not in EMOJI_GROUPS:
            self.log_error(f"Unknown group: {group_name}")
            return

        ranges = EMOJI_GROUPS[group_name]

        self.log_info(f"Group: {group_name}")
        self.log_info("")

        count = 0
        row = []

        def flush_row():
            if not row:
                return
            self.log_info(spacing.join(row))
            row.clear()

        for start, end in ranges:
            for codepoint in range(start, end + 1):
                try:
                    ch = chr(codepoint)
                except Exception:
                    continue

                if show_code:
                    cell = f"{ch}({hex(codepoint)})"
                else:
                    cell = ch

                row.append(cell)
                count += 1

                if len(row) >= columns:
                    flush_row()

                if max_count > 0 and count >= max_count:
                    flush_row()
                    self.log_info("")
                    self.log_info(f"Stopped at max_count={max_count}")
                    return

        flush_row()

        self.log_info("")
        self.log_info(f"Total emojis printed: {count}")


# -------------------------
# ENTRY
# -------------------------
if __name__ == "__main__":
    EmojiScript().execute()