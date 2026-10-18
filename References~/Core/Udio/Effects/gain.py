from pydub import AudioSegment

def apply_gain(input_audio, amount, start_time=None, end_time=None, in_crossfade=0, out_crossfade=0):
    """
    Adjusts the volume of the audio track with optional start and end times.
    
    - `amount`: Gain level in dB (positive increases volume, negative decreases).
    - `start_time`: Start applying gain from this time (in ms).
    - `end_time`: Stop applying gain at this time (in ms).
    - `in_crossfade`: Smoothly applies the volume change over time (in ms).
    - `out_crossfade`: Smoothly removes the volume change over time (in ms).

    Returns:
        Modified audio with gain applied to a specific section or the entire track.
    """

    # **Clamp gain value to a reasonable range (-30dB to +30dB)**
    amount = max(min(amount, 30), -30)  # Prevent excessive clipping or inaudibility

    # Set default start_time and end_time
    if start_time is None:
        start_time = 0  # Default: Apply from beginning
    if end_time is None or end_time > len(input_audio):
        end_time = len(input_audio)  # Default: Apply until end

    # Split audio into three parts: BEFORE, TARGET, AFTER
    before_gain = input_audio[:start_time]  # Before gain effect
    target_gain = input_audio[start_time:end_time] + amount  # Apply gain
    after_gain = input_audio[end_time:]  # After gain effect

    # **Apply smooth entry (fade-in) if specified**
    if in_crossfade > 0:
        before_gain = before_gain.append(target_gain[:in_crossfade].fade_in(in_crossfade), crossfade=in_crossfade)
        target_gain = target_gain[in_crossfade:]  # Remove the crossfade part from target

    # **Apply smooth exit (fade-out) if specified**
    if out_crossfade > 0:
        target_gain = target_gain[:-out_crossfade]  # Remove fade-out part
        after_gain = target_gain[-out_crossfade:].fade_out(out_crossfade).append(after_gain, crossfade=out_crossfade)

    # Combine all parts
    modified_audio = before_gain + target_gain + after_gain

    return modified_audio

effect_name = {"gain": apply_gain}
