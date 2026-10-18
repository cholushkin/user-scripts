from pydub import AudioSegment

def apply_fade_in(input_audio, time):
    """Applies fade-in effect to the audio."""
    return input_audio.fade_in(time)

def apply_fade_out(input_audio, time):
    """Applies fade-out effect to the audio."""
    return input_audio.fade_out(time)

effect_name = {
    "fade_in": apply_fade_in,
    "fade_out": apply_fade_out
}
