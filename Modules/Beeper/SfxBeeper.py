import numpy as np
import sounddevice as sd
import json
import argparse
import time

SAMPLE_RATE = 44100


# ---------- HELPERS ----------

def clamp(val, min_val, max_val):
    return max(min_val, min(max_val, val))


# ---------- MAIN CLASS ----------

class BeepSfx:
    def __init__(
        self,
        freq=440,
        length=1.0,

        wave_type="square",

        # ADSR
        attack=0.01,
        decay=0.1,
        sustain=0.7,
        release=0.3,

        volume=0.3,
        delay=0.0,
        pan=0.0,
    ):
        self.freq = clamp(freq, 20, 20000)
        self.length = clamp(length, 0.01, 5.0)

        self.wave_type = wave_type if wave_type in ["square", "triangle", "sine"] else "square"

        # ADSR
        self.attack = max(0.0, attack)
        self.decay = max(0.0, decay)
        self.sustain = clamp(sustain, 0.0, 1.0)
        self.release = max(0.0, release)

        self.volume = clamp(volume, 0.0, 1.0)
        self.delay = clamp(delay, 0.0, 1.0)
        self.pan = clamp(pan, -1.0, 1.0)

        self._fix_adsr()

    # ---------- FIX ADSR ----------

    def _fix_adsr(self):
        total = self.attack + self.decay + self.release

        # if ADSR exceeds length → scale it down
        if total > self.length:
            scale = self.length / total
            self.attack *= scale
            self.decay *= scale
            self.release *= scale

        # ensure there is always some sustain time
        sustain_time = self.length - (self.attack + self.decay + self.release)
        if sustain_time < 0:
            # fallback: no sustain
            self.release = max(0.0, self.length - (self.attack + self.decay))

    # ---------- WAVE ----------

    def generate_wave(self):
        n = int(SAMPLE_RATE * self.length)
        t = np.linspace(0, self.length, n, False)

        if self.wave_type == "square":
            wave = np.sign(np.sin(2 * np.pi * self.freq * t))
        elif self.wave_type == "triangle":
            wave = 2 * np.arcsin(np.sin(2 * np.pi * self.freq * t)) / np.pi
        else:
            wave = np.sin(2 * np.pi * self.freq * t)

        return wave.astype(np.float32)

    # ---------- ADSR ENVELOPE ----------

    def apply_envelope(self, wave):
        length = len(wave)
        env = np.zeros(length, dtype=np.float32)

        a = int(self.attack * SAMPLE_RATE)
        d = int(self.decay * SAMPLE_RATE)
        r = int(self.release * SAMPLE_RATE)

        s = length - (a + d + r)
        s = max(0, s)

        pos = 0

        # ATTACK (0 → 1)
        if a > 0:
            env[pos:pos + a] = np.linspace(0, 1, a)
            pos += a

        # DECAY (1 → sustain level)
        if d > 0:
            env[pos:pos + d] = np.linspace(1, self.sustain, d)
            pos += d

        # SUSTAIN (constant)
        if s > 0:
            env[pos:pos + s] = self.sustain
            pos += s

        # RELEASE (sustain → 0)
        if r > 0:
            env[pos:pos + r] = np.linspace(self.sustain, 0, r)

        return wave * env

    # ---------- PAN ----------

    def apply_pan(self, mono):
        left = mono * (1 - max(0, self.pan))
        right = mono * (1 + min(0, self.pan))
        return np.column_stack((left, right))

    # ---------- DELAY ----------

    def apply_delay(self, stereo):
        delay_samples = int(self.delay * SAMPLE_RATE)

        if delay_samples <= 0:
            return stereo

        pad = np.zeros((delay_samples, 2), dtype=np.float32)
        return np.vstack((pad, stereo))

    # ---------- GENERATE ----------

    def generate(self):
        wave = self.generate_wave()
        wave = self.apply_envelope(wave)
        wave *= self.volume

        stereo = self.apply_pan(wave)
        stereo = self.apply_delay(stereo)

        return stereo

    # ---------- DEBUG ----------

    def to_dict(self):
        return {
            "freq": round(self.freq, 3),
            "length": round(self.length, 3),
            "wave_type": self.wave_type,
            "attack": round(self.attack, 3),
            "decay": round(self.decay, 3),
            "sustain": round(self.sustain, 3),
            "release": round(self.release, 3),
            "volume": round(self.volume, 3),
            "delay": round(self.delay, 3),
            "pan": round(self.pan, 3),
        }

    def print_params(self):
        params = self.to_dict()

        print("\n--- SOUND PARAMS ---")
        print(json.dumps(params, indent=2))

        args = ", ".join(f"{k}={repr(v)}" for k, v in params.items())
        print("\n# Copy-paste:")
        print(f"BeepSfx({args})")


# ---------- RANDOM ----------

def random_sfx(rng):
    length = rng.uniform(0.5, 0.85)

    attack = rng.uniform(0.01, 0.05)
    decay = rng.uniform(0.05, 0.2)
    sustain = rng.uniform(0.5, 0.9)
    release = rng.uniform(0.3, 0.8)

    sfx = BeepSfx(
        freq=rng.uniform(200, 1200),
        length=length,
        wave_type=rng.choice(["square", "triangle", "sine"]),
        attack=attack,
        decay=decay,
        sustain=sustain,
        release=release,
        volume=rng.uniform(0.2, 0.4),
        delay=rng.uniform(0.0, 0.05),
        pan=rng.uniform(-1.0, 1.0),
    )

    sfx.print_params()
    return sfx


# ---------- MIX ----------

def mix_sounds(sfx_list):
    generated = [s.generate() for s in sfx_list]

    max_len = max(s.shape[0] for s in generated)

    padded = []
    for s in generated:
        pad_len = max_len - s.shape[0]
        if pad_len > 0:
            pad = np.zeros((pad_len, 2), dtype=np.float32)
            s = np.vstack((s, pad))
        padded.append(s)

    mix = np.sum(padded, axis=0)

    # ⚠️ softer normalization (optional tweak)
    peak = np.max(np.abs(mix))
    if peak > 1.0:
        mix /= peak

    return mix * 0.5


def play(sound):
    sd.play(sound, SAMPLE_RATE)
    sd.wait()


# ---------- CLI ----------

def parse_args():
    parser = argparse.ArgumentParser(description="Procedural SFX generator")

    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--count", type=int, default=2)
    parser.add_argument("--merged-only", action="store_true")

    return parser.parse_args()


# ---------- MAIN ----------

if __name__ == "__main__":
    args = parse_args()

    seed = args.seed if args.seed is not None else int(time.time())
    rng = np.random.default_rng(seed)

    print(f"\n🌱 SEED: {seed}")

    print(f"\n=== GENERATING {args.count} SOUNDS ===")
    sounds = [random_sfx(rng) for _ in range(args.count)]

    if not args.merged_only:
        print("\n=== PLAYING INDIVIDUALLY ===")
        for s in sounds:
            play(s.generate())

    print("\n=== PLAYING MIXED ===")
    mixed = mix_sounds(sounds)
    play(mixed)