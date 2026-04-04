import time
import numpy as np
import sounddevice as sd

from SeqParser import SequenceParser, build_timeline
from SfxBeeper import BeepSfx, SAMPLE_RATE


# -------------------------
# CONFIG
# -------------------------

SLOT_DURATION = 1.0  # seconds per slot

# freq (Hz), duration (sec), volume (0–1)
DEFINITIONS = {
    "M": (880, 0.8, 0.3),
    "K": (660, 0.6, 0.3),
    "H": (1200, 0.3, 0.25),

    # 🔥 tick (audible marker)
    "S": (1500, 0.03, 0.4),

    # 🔥 real silence
    "_": (0, 0.01, 0.0),
}

SEQUENCE = "M3 (H S7 K)*5"


# -------------------------
# ENGINE
# -------------------------

class Beeper:
    def __init__(self, definitions, sequence, slot_duration=1.0):
        self.slot_duration = slot_duration

        # Parse DSL → timeline
        tokens = SequenceParser(sequence).parse()
        self.timeline = build_timeline(tokens)

        # Pre-generate clips
        self.clips = self.build_clips(definitions)

        # Active playing sounds
        self.active = []

    # -------------------------
    # BUILD CLIPS
    # -------------------------

    def build_clips(self, definitions):
        clips = {}

        for name, (freq, length, volume) in definitions.items():
            length = min(length, 0.99)

            # true silence
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

    # -------------------------
    # AUDIO CALLBACK
    # -------------------------

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

        # soft normalize
        peak = np.max(np.abs(buffer))
        if peak > 1.0:
            buffer /= peak

        outdata[:] = buffer

    # -------------------------
    # VISUAL
    # -------------------------

    def render(self, index):
        out = []

        for i, t in enumerate(self.timeline):
            if i < index:
                out.append(f"\033[92m{t}\033[0m")
            elif i == index:
                out.append(f"\033[97m[{t}]\033[0m")
            else:
                out.append(f"\033[90m{t}\033[0m")

        print("\r" + " ".join(out), end="", flush=True)

    # -------------------------
    # RUN
    # -------------------------

    def run(self):
        print("\nSequence :", SEQUENCE)
        print("Timeline :", " ".join(self.timeline))
        print(f"Slot duration: {self.slot_duration}s\n")

        with sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=2,
            dtype="float32",
            callback=self.callback,
        ):
            start_time = time.time()

            for i, step in enumerate(self.timeline):
                target_time = start_time + i * self.slot_duration

                while time.time() < target_time:
                    time.sleep(0.001)

                if step in self.clips:
                    self.active.append((self.clips[step], 0))

                self.render(i)

            # let sounds finish
            time.sleep(1.5)

        print("\nDone.")


# -------------------------
# MAIN
# -------------------------

if __name__ == "__main__":
    Beeper(DEFINITIONS, SEQUENCE, SLOT_DURATION).run()