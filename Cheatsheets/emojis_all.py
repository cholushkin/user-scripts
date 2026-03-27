import sys

# Unicode ranges that cover most emojis
emoji_ranges = [
    (0x1F600, 0x1F64F),  # Emoticons
    (0x1F300, 0x1F5FF),  # Misc Symbols & Pictographs
    (0x1F680, 0x1F6FF),  # Transport & Map Symbols
    (0x1F700, 0x1F77F),  # Alchemical Symbols
    (0x1F780, 0x1F7FF),  # Geometric Shapes Extended
    (0x1F800, 0x1F8FF),  # Supplemental Arrows-C
    (0x1F900, 0x1F9FF),  # Supplemental Symbols & Pictographs
    (0x1FA00, 0x1FAFF),  # Chess Symbols, etc.
    (0x1FB00, 0x1FBFF),  # Symbols for Legacy Computing
    (0x2600, 0x26FF),    # Misc symbols
    (0x2700, 0x27BF),    # Dingbats
]

for start, end in emoji_ranges:
    for codepoint in range(start, end + 1):
        try:
            sys.stdout.write(chr(codepoint))
        except:
            pass

sys.stdout.flush()
