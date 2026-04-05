# Beeper

## Quick Start (CLI)

```
beeper --sequence "r s g (M S5 K)*2" --slot_duration 1.0
```

### Parameters

- `sequence` — DSL string describing timeline
- `slot_duration` — duration of one step (seconds)
- `loop` — repeat full sequence
- `dry_run` — print timeline only (no playback)

---

## What it does

Beeper:

1. Parses `sequence` → timeline (list of steps)
2. Prints timeline in terminal
3. Opens player window
4. Plays audio + visualizes progress

---

## Examples

### Countdown

```
beeper --sequence "r s g"
```

### Workout intervals

```
beeper --sequence "(M S5 K)*4"
```

### Pomodoro (simplified)

```
beeper --sequence "2*(M*1500 R*300)"
```

### Metronome

```
beeper --sequence "M*100" --slot_duration 0.5
```

---

## Sequence DSL

### Tokens

Each token maps to a sound or speech:

```
M K S r s g R
```

### Repetition

```
M3        # repeat 3 times
M*3       # same
```

### Groups

```
(M S K)*2
2*(M S K)
```

### Combined

```
r s g (M S5 K)*2
```

---

## Architecture

### Process model

Two processes:

1. **BeeperScript (main)**
   - parses parameters
   - builds timeline
   - prints timeline
   - launches player

2. **BeeperPlayerUI (subprocess)**
   - creates DearPyGui context
   - runs playback loop
   - renders timeline

Reason:
- DearPyGui supports one context per process

---

## Core modules

### `SequenceParser`

- parses DSL string
- outputs tokens
- used by `build_timeline`

### `build_timeline`

- expands tokens into flat list

```
["M", "S", "S", "K"]
```

---

### `BeeperEngine`

- builds audio clips (from `DEFINITIONS`)
- manages active sounds
- sounddevice callback mixer
- timing based on `slot_duration`

Key methods:

- `start()`
- `update()`
- `callback()`
- `stop()`

---

### `BeeperPlayerUI`

- DearPyGui window
- displays timeline
- updates colors per frame
- drives `BeeperEngine.update()`

---

### `speech_engine`

- generates TTS `.wav`
- loads audio into numpy
- cleans temp files

---

## Data flow

```
sequence (string)
    ↓
SequenceParser
    ↓
tokens
    ↓
build_timeline
    ↓
timeline (list[str])
    ↓
BeeperEngine
    ↓
audio + UI
```

---

## Timing model

- each step = `slot_duration`
- index = floor((time - start) / slot_duration)
- step triggers sound once

---

## Notes

- timeline is precomputed
- sounds can overlap
- playback ends after last sound tail
