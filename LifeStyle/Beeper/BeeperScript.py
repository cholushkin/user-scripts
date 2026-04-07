import sys
import os
import time
import json
import subprocess
import numpy as np
import sounddevice as sd

# -------------------------
# PATH SETUP
# -------------------------
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Shared")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from base_script import BaseScript
from context import ParamGroup
from param import Param

from SeqParser import SequenceParser, build_timeline
from SfxBeeper import BeepSfx, SAMPLE_RATE
from speech_engine import Speech

import dearpygui.dearpygui as dpg


# -------------------------
# DEFAULTS
# -------------------------
DEFAULTS = {
    "sequence": "r s g (M S5 K)*1",
    "slot_duration": 1.0,
    "loop": 1,
    "dry_run": False,
}


# -------------------------
# DEFINITIONS
# -------------------------
DEFINITIONS = {
    "M": (880, 0.8, 0.3),
    "K": (1200, 0.8, 0.3),
    "S": (1500, 0.03, 0.4),
    "_": (0, 0.01, 0.0),

    "R": ("Rest", 1.5, 1.0),
    "r": ("Ready", 1.0, 1.0),
    "s": ("Set", 1.0, 1.0),
    "g": ("Go", 1.0, 1.0),
    "Z": ("Stop", 1.0, 1.0),
}


# =========================================================
# 🔊 ENGINE (PLAYER PROCESS ONLY)
# =========================================================
class BeeperEngine:

    def __init__(self, timeline, slot_duration):
        self.timeline = timeline
        self.slot_duration = slot_duration

        self.clips = self.build_clips(DEFINITIONS)
        self.active = []

        self.current_index = -1
        self.start_time = None
        self.stream = None

    def build_clips(self, definitions):
        clips = {}
        speech_jobs = {}

        for name, val in definitions.items():
            if isinstance(val[0], str):
                text, duration, volume = val
                speech_jobs[name] = (Speech.prepare(text), duration, volume)

        if speech_jobs:
            Speech.generate_all()

        for name, val in definitions.items():

            if isinstance(val[0], str):
                filepath, target_duration, volume = speech_jobs[name]
                samples = Speech.load_numpy(filepath, SAMPLE_RATE)
                samples *= volume

                target_len = int(target_duration * SAMPLE_RATE)

                if len(samples) > target_len:
                    samples = samples[:target_len]
                elif len(samples) < target_len:
                    pad = np.zeros((target_len - len(samples), 2), dtype=np.float32)
                    samples = np.vstack((samples, pad))

                clips[name] = samples
                continue

            freq, length, volume = val

            if volume <= 0 or freq <= 0:
                clips[name] = np.zeros((1, 2), dtype=np.float32)
                continue

            clips[name] = BeepSfx(
                freq=freq,
                length=length,
                volume=volume,
                wave_type="square",
            ).generate()

        return clips

    def callback(self, outdata, frames, time_info, status):
        buffer = np.zeros((frames, 2), dtype=np.float32)
        new_active = []

        for sound, pos in self.active:
            remaining = len(sound) - pos
            n = min(frames, remaining)

            if n > 0:
                buffer[:n] += sound[pos:pos + n]

            if pos + n < len(sound):
                new_active.append((sound, pos + n))

        self.active = new_active

        peak = np.max(np.abs(buffer))
        if peak > 1.0:
            buffer /= peak

        outdata[:] = buffer

    def start(self):
        self.stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=2,
            dtype="float32",
            callback=self.callback,
        )
        self.stream.start()
        self.start_time = time.time()

    def update(self):
        if self.start_time is None:
            return

        elapsed = time.time() - self.start_time
        index = int(elapsed / self.slot_duration)

        if index != self.current_index and index < len(self.timeline):
            self.current_index = index
            step = self.timeline[index]

            if step in self.clips:
                self.active.append((self.clips[step], 0))

    def is_finished(self):
        return self.current_index >= len(self.timeline) - 1

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
        Speech.cleanup()


# =========================================================
# 🎨 PLAYER UI (SECOND PROCESS)
# =========================================================
class BeeperPlayerUI:

    def __init__(self, timeline, slot_duration):
        self.engine = BeeperEngine(timeline, slot_duration)

    def run(self):
        dpg.create_context()

        with dpg.window(label="Beeper Player", width=900, height=200):
            self.texts = []
            with dpg.group(horizontal=True):
                for t in self.engine.timeline:
                    txt = dpg.add_text(t)
                    self.texts.append(txt)

        dpg.create_viewport(title="Beeper", width=920, height=220)
        dpg.setup_dearpygui()
        dpg.show_viewport()

        self.engine.start()

        while dpg.is_dearpygui_running():
            self.engine.update()

            for i, txt in enumerate(self.texts):
                if i < self.engine.current_index:
                    dpg.configure_item(txt, color=(0, 255, 0))
                elif i == self.engine.current_index:
                    dpg.configure_item(txt, color=(255, 255, 255))
                else:
                    dpg.configure_item(txt, color=(120, 120, 120))

            dpg.render_dearpygui_frame()

            if self.engine.is_finished():
                # wait for sound tail
                if not self.engine.active:
                    break

        self.engine.stop()
        dpg.destroy_context()


# =========================================================
# 🧠 SCRIPT (MAIN PROCESS)
# =========================================================
class BeeperScript(BaseScript):

    def define_groups(self):
        return [
            ParamGroup("Playback", [
                Param("sequence", str, DEFAULTS["sequence"]),
                Param("slot_duration", float, DEFAULTS["slot_duration"]),
                Param("loop", int, DEFAULTS["loop"]),
                Param("dry_run", bool, DEFAULTS["dry_run"]),
            ])
        ]

    def get_defaults(self):
        return DEFAULTS

    def preview(self, ctx):
        try:
            tokens = SequenceParser(ctx["sequence"]).parse()
            timeline = build_timeline(tokens)
            return " ".join(timeline[:30])
        except Exception as e:
            return f"[ERR] {e}"

    def run(self, ctx):
        sequence = ctx["sequence"]
        slot_duration = ctx["slot_duration"]
        loop = max(1, ctx["loop"])
        dry_run = ctx["dry_run"]

        tokens = SequenceParser(sequence).parse()
        timeline = build_timeline(tokens) * loop

        # 🔥 PRINT TIMELINE (requested)
        print("\nTIMELINE:")
        print(" ".join(timeline))
        print()

        if dry_run:
            return

        # 🔥 launch player process
        payload = json.dumps({
            "timeline": timeline,
            "slot": slot_duration,
        })

        subprocess.Popen([
            sys.executable,
            __file__,
            "--player",
            payload
        ])

        # 🔥 kill UI process immediately
        os._exit(0)


# =========================================================
# 🚀 ENTRY
# =========================================================
if __name__ == "__main__":

    if "--player" in sys.argv:
        idx = sys.argv.index("--player")
        payload = json.loads(sys.argv[idx + 1])

        BeeperPlayerUI(
            payload["timeline"],
            payload["slot"]
        ).run()

        sys.exit(0)

    BeeperScript().execute()