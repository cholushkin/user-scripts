import pyttsx3
from pydub import AudioSegment
import os
import uuid
import numpy as np


# -------------------------
# 🔥 STARTUP CLEANUP
# -------------------------

def _cleanup_old_wavs():
    cwd = os.getcwd()

    for f in os.listdir(cwd):
        if f.endswith(".wav"):
            try:
                os.remove(os.path.join(cwd, f))
            except:
                pass


# run immediately on import
_cleanup_old_wavs()


# -------------------------
# SPEECH ENGINE
# -------------------------

class Speech:
    _engine = pyttsx3.init()
    _generated_files = []

    @staticmethod
    def prepare(text: str, rate: int = 200):
        filename = f"tts_{uuid.uuid4()}.wav"
        filepath = os.path.join(os.getcwd(), filename)

        Speech._generated_files.append(filepath)

        Speech._engine.setProperty('rate', rate)
        Speech._engine.save_to_file(text, filepath)

        return filepath

    @staticmethod
    def generate_all():
        Speech._engine.runAndWait()

    @staticmethod
    def load_numpy(filepath: str, target_rate: int):
        seg = AudioSegment.from_wav(filepath)

        # 🔥 resample to match engine
        if seg.frame_rate != target_rate:
            seg = seg.set_frame_rate(target_rate)

        samples = np.array(seg.get_array_of_samples()).astype(np.float32)

        if seg.channels == 2:
            samples = samples.reshape((-1, 2))
        else:
            samples = np.column_stack((samples, samples))

        # normalize
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            samples /= max_val

        return samples

    @staticmethod
    def cleanup():
        for f in Speech._generated_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
        Speech._generated_files.clear()