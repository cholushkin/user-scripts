import sys
import os

# -------------------------
# PATH SETUP
# -------------------------
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Shared")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from base_script import BaseScript
from context import ParamGroup
from param import Param

from SeqParser import SequenceParser, build_timeline
from Beeper import Beeper, DEFINITIONS


# -------------------------
# DEFAULTS
# -------------------------
DEFAULTS = {
    "sequence": "r s g (M S5 K)*1",
    "slot_duration": 1.0,
    "loop": 1,
    "dry_run": False,
    "show_timeline": False,
}


# -------------------------
# SCRIPT
# -------------------------
class BeeperScript(BaseScript):

    # -------------------------
    # PARAMS
    # -------------------------
    def define_groups(self):
        return [
            ParamGroup("Playback", [
                Param("sequence", str, DEFAULTS["sequence"],
                      description="Sequence DSL (tokens, groups, repeats)"),

                Param("slot_duration", float, DEFAULTS["slot_duration"],
                      description="Duration of one timeline slot (seconds)"),

                Param("loop", int, DEFAULTS["loop"],
                      description="How many times to repeat full sequence"),

                Param("dry_run", bool, DEFAULTS["dry_run"],
                      description="Do not play audio, only print timeline"),

                Param("show_timeline", bool, DEFAULTS["show_timeline"],
                      description="Print parsed timeline before playback"),
            ])
        ]

    # -------------------------
    def get_defaults(self):
        return DEFAULTS

    # -------------------------
    # PREVIEW (UI)
    # -------------------------
    def preview(self, ctx):
        try:
            tokens = SequenceParser(ctx["sequence"]).parse()
            timeline = build_timeline(tokens)
            preview = " ".join(timeline[:30])
            if len(timeline) > 30:
                preview += " ..."
            return preview
        except Exception as e:
            return f"[ERR] {e}"

    # -------------------------
    # RUN
    # -------------------------
    def run(self, ctx):
        sequence = ctx["sequence"]
        slot_duration = ctx["slot_duration"]
        loop = max(1, ctx["loop"])
        dry_run = ctx["dry_run"]
        show_timeline = ctx["show_timeline"]

        # -------------------------
        # PARSE
        # -------------------------
        try:
            tokens = SequenceParser(sequence).parse()
            timeline = build_timeline(tokens)
        except Exception as e:
            self.log_error(f"Parse error: {e}")
            return

        full_timeline = timeline * loop

        # -------------------------
        # LOG INFO
        # -------------------------
        if show_timeline:
            self.log_info("")
            self.log_info("Timeline:")
            self.log_info(" ".join(full_timeline))

        # -------------------------
        # DRY RUN
        # -------------------------
        if dry_run:
            self.log_info("")
            self.log_info("[DRY RUN] No audio played")
            return

        # -------------------------
        # PLAY
        # -------------------------
        beeper = Beeper(DEFINITIONS, sequence, slot_duration)

        # override generated timeline with looped one
        beeper.timeline = full_timeline

        beeper.run()


# -------------------------
# ENTRY
# -------------------------
if __name__ == "__main__":
    BeeperScript().execute()