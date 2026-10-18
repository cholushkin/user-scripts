from pydub import AudioSegment

def apply_cut_beginning(input_audio, time):
    """Removes the first `time` milliseconds of the audio."""
    return input_audio[time:]

def apply_cut_end(input_audio, time):
    """Removes the last `time` milliseconds of the audio."""
    return input_audio[:-time]

effect_name = {
    "cut_beginning": apply_cut_beginning,
    "cut_end": apply_cut_end
}
