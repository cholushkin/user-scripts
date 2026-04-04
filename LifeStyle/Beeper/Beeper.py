import time
import numpy as np
import sounddevice as sd

from SeqParser import SequenceParser, build_timeline
from SfxBeeper import BeepSfx, SAMPLE_RATE
from speech_engine import Speech


# -------------------------
# CONFIG
# -------------------------

SLOT_DURATION = 1.0

DEFINITIONS = {
    "M": (880, 0.8, 0.3),
    "K": (1200, 0.8, 0.3),

    "S": (1500, 0.03, 0.4),
    "_": (0, 0.01, 0.0),

    # 🔥 speech: (text, duration, volume)
    "R": ("Rest now", 1.5, 1.0),
    "r": ("Ready", 1.0, 1.0),
    "s": ("Set", 1.0, 1.0),
    "g": ("Go", 1.0, 1.0),
    "Z": ("Stop", 1.0, 1.0),
}

SEQUENCE = "r s g (M S5 K)*7"


# -------------------------
# ENGINE
# -------------------------

class Beeper:
    def __init__(self, definitions, sequence, slot_duration=1.0):
        self.slot_duration = slot_duration

        tokens = SequenceParser(sequence).parse()
        self.timeline = build_timeline(tokens)

        self.clips = self.build_clips(definitions)
        self.active = []

    # -------------------------
    # BUILD CLIPS
    # -------------------------

    def build_clips(self, definitions):
        clips = {}
        speech_jobs = {}

        # prepare speech
        for name, val in definitions.items():
            if isinstance(val[0], str):
                text, duration, volume = val
                speech_jobs[name] = (Speech.prepare(text), duration, volume)

        if speech_jobs:
            Speech.generate_all()

        # build clips
        for name, val in definitions.items():

            # ---------- SPEECH ----------
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

            # ---------- SOUND ----------
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

            time.sleep(2.0)

        print("\nDone.")
        Speech.cleanup()


# -------------------------
# MAIN
# -------------------------

if __name__ == "__main__":
    Beeper(DEFINITIONS, SEQUENCE, SLOT_DURATION).run()