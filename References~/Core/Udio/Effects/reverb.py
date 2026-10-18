import os
import subprocess
from pydub import AudioSegment

def apply_reverb(input_audio, amount, start_time=None, end_time=None, in_crossfade=0, out_crossfade=0):
    """
    Applies reverb using Sox (external processing).
    - amount: Reverb intensity (0-100)
    - start_time: When the reverb starts (in milliseconds) (default: entire track)
    - end_time: When the reverb stops (in milliseconds) (default: entire track)
    - in_crossfade: Smoothly enters the reverb effect (milliseconds)
    - out_crossfade: Smoothly exits the reverb effect (milliseconds)
    """
    temp_input = "temp_input.wav"
    temp_output = "temp_output.wav"

    input_audio.export(temp_input, format="wav")  # Save temp file

    sox_command = [
        "sox", temp_input, temp_output,
        "reverb", str(amount),  
        "gain", "-5"
    ]

    try:
        subprocess.run(sox_command, check=True)
        reverb_audio = AudioSegment.from_wav(temp_output)

        # Set default start_time and end_time
        if start_time is None:
            start_time = 0  # Default: Start at beginning
        if end_time is None or end_time > len(reverb_audio):
            end_time = len(reverb_audio)  # Default: Apply to entire track

        # Trim reverb effect within the given time range
        reverb_audio = reverb_audio[start_time:end_time]

        # Apply crossfades if specified
        if in_crossfade > 0:
            reverb_audio = reverb_audio.fade_in(in_crossfade)
        if out_crossfade > 0:
            reverb_audio = reverb_audio.fade_out(out_crossfade)

        return reverb_audio

    except subprocess.CalledProcessError as e:
        print(f"Error applying reverb: {e}")
        return input_audio  # Return original audio if error

    finally:
        os.remove(temp_input)
        if os.path.exists(temp_output):
            os.remove(temp_output)

effect_name = { "reverb": apply_reverb }
