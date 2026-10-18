import pyttsx3
from pydub import AudioSegment
import os
import uuid
import numpy as np


# -------------------------
# BASE DIR (FIXED LOCATION)
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# -------------------------
# CLEANUP (ONLY LOCAL FILES)
# -------------------------
def _cleanup_old_wavs():
    for f in os.listdir(BASE_DIR):
        if f.endswith(".wav"):
            try:
                os.remove(os.path.join(BASE_DIR, f))
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

    # -------------------------
    # PREPARE (QUEUE TTS)
    # -------------------------
    @staticmethod
    def prepare(text: str, rate: int = 200):
        filename = f"tts_{uuid.uuid4()}.wav"
        filepath = os.path.join(BASE_DIR, filename)  # 🔥 FIXED PATH

        Speech._generated_files.append(filepath)

        Speech._engine.setProperty('rate', rate)
        Speech._engine.save_to_file(text, filepath)

        return filepath

    # -------------------------
    # GENERATE ALL (EXECUTE TTS)
    # -------------------------
    @staticmethod
    def generate_all():
        Speech._engine.runAndWait()

    # -------------------------
    # LOAD AS NUMPY
    # -------------------------
    @staticmethod
    def load_numpy(filepath: str, target_rate: int):
        seg = AudioSegment.from_wav(filepath)

        # resample if needed
        if seg.frame_rate != target_rate:
            seg = seg.set_frame_rate(target_rate)

        samples = np.array(seg.get_array_of_samples()).astype(np.float32)

        # stereo handling
        if seg.channels == 2:
            samples = samples.reshape((-1, 2))
        else:
            samples = np.column_stack((samples, samples))

        # normalize
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            samples /= max_val

        return samples

    # -------------------------
    # CLEANUP (ONLY GENERATED)
    # -------------------------
    @staticmethod
    def cleanup():
        for f in Speech._generated_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
        Speech._generated_files.clear()