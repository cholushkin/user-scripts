# Udio

Audio-stem mixing/export pipeline for music tracks: ingest raw stem exports, mix them
with a small effects system, analyze the resulting MP3 library, and export finished
tracks into a Unity project. Ported from the old `ScriptUtils/Core/Udio`, split into
four separate commands (the original Core classes).

## Typical workflow

```
udio-add     → organize raw .mp3/.zip pairs into per-track folders + default JSON configs
udio-mix     → extract stems, apply effects, overlay, export mixed MP3s
udio-analyze → audit the resulting track library (duration, size, duplicates)
udio-export  → copy finished tracks (+ metadata) into a Unity project
```

Each command is its own `BaseScript`, with its own params/presets/interactive UI
(hold **Left Ctrl**, or pass `--interactive`).

## Dependencies (not installed by this tool)

- [`pydub`](https://pypi.org/project/pydub/) — audio loading, overlay, export.
- [`mutagen`](https://pypi.org/project/mutagen/) — MP3 duration reading (`udio-analyze`).
- `ffmpeg` on `PATH` — required by `pydub` for MP3 export/decoding.
- `sox` on `PATH` — only needed for the `reverb` effect.

---

## `udio-add` — AddNewTracksScript

Moves (or copies) matching `.mp3`/`.zip` pairs from a flat source folder into numbered
per-track subfolders under a target root, generating a default track JSON (from the
bundled `AddNewTracksJsonTemplate.json`) for each one.

```
udio-add --source_directory "Inbox" --track_target_path "tracks" --move_files
```

| Param | Default | Description |
| --- | --- | --- |
| `source_directory` | `""` | Folder with the raw `.mp3`/`.zip` pairs (relative to `--cwd`, or absolute). |
| `track_target_path` | `""` | Folder where per-track subfolders are created. |
| `move_files` | `True` | Move the source files; if `False`, copy them instead. |

Every `.mp3` must have a matching `.zip` with the same base name (and vice versa) or the
whole run is rejected with a list of the mismatches. Matched pairs are renamed
`<Name> <N>.mp3` / `<Name> <N>.zip` inside `<track_target_path>/<Name>/`, with `<N>`
auto-incremented past any existing numbered files in that folder.

---

## `udio-mix` — MixTracksScript

Finds every track JSON under `look_folders`, extracts its stem ZIP, applies effects, and
overlays the stems into a final MP3.

```
udio-mix --look_folders "tracks"
```

| Param | Default | Description |
| --- | --- | --- |
| `look_folders` | `""` | Folders to search for track JSON configs (semicolon-separated). |
| `override_target_wildcard` | `""` | Optional glob patterns (semicolon-separated) matched against each JSON's filename. Blank = the override applies to every track. |
| `override_json` | `""` | Optional raw JSON object merged into each matched track's `mix` section — e.g. to force a one-off re-mix of normally-`ignore`d tracks. |
| `default_bitrate` | `192k` | MP3 export bitrate used when a track's JSON doesn't specify one. |

Each ZIP must contain exactly `bass.wav`, `drums.wav`, `other.wav`, `vocals.wav` — any
missing stem fails that track (strict validation, no partial mixes). A track with
`"ignore": true` in its `mix` section (after overrides are applied) is skipped.

---

## `udio-export` — ExportTracksScript

Copies finished MP3s (that have `export_parameters.export != false`) from `look_folders`
into a Unity project, alongside a simplified `<track>.meta.json` (`tags` + the configured
`music_configuration` name) for the engine side to pick up.

```
udio-export --look_folders "tracks" --unity_dest_path "Assets/Audio/Music" --music_configuration "MusicConfig"
```

| Param | Default | Description |
| --- | --- | --- |
| `look_folders` | `""` | Folders to search for track JSON configs (semicolon-separated). |
| `unity_dest_path` | `""` | Destination folder for exported tracks, relative to the resolved Unity root. |
| `music_configuration` | `""` | Name of the music configuration asset to reference in each track's metadata JSON. |
| `unity_root` | `""` | Optional override. Blank = resolved via the discovered `.uscript` project's asset folder (replaces the old global `unity_project_root` config key — see `Modules/KritaExport`, which uses the same discovery). |

---

## `udio-analyze` — AnalyzeTrackDBScript

Scans `look_folders` for `.mp3` files with a matching `.json`, and reports duration/size
totals, estimated size at other bitrates, and duplicate files (by MD5 content hash and
by filename).

```
udio-analyze --look_folders "tracks" --estimate_bitrates "128k;192k;256k;320k"
```

| Param | Default | Description |
| --- | --- | --- |
| `look_folders` | `""` | Folders to scan for MP3/JSON track pairs (semicolon-separated). |
| `estimate_bitrates` | `128k;192k;256k;320k` | Bitrates to estimate total library size at (semicolon-separated). |

MP3s without a matching `.json` are reported and skipped — the analysis is metadata-driven.

---

## Effects system (`Effects/`)

Each file in `Modules/Udio/Effects/` is dynamically loaded by `udio-mix` and must export
an `effect_name = {"name": function}` dict. Built-in effects:

| Effect | File | Signature |
| --- | --- | --- |
| `gain` | `gain.py` | `(audio, amount, start_time=None, end_time=None, in_crossfade=0, out_crossfade=0)` — volume change in dB (±30 clamp), optionally scoped to a time range with crossfades. |
| `fade_in`, `fade_out` | `fade.py` | `(audio, time)` — fade over `time` ms. |
| `cut_beginning`, `cut_end` | `cut.py` | `(audio, time)` — trim `time` ms from the start/end. |
| `reverb` | `reverb.py` | `(audio, amount, start_time=None, end_time=None, in_crossfade=0, out_crossfade=0)` — via external `sox`. |

A track's JSON references effects by name under `mix.effects`, each with its own
`target_track` (one of the 4 stem filenames, or omitted to apply to all stems) plus
whatever kwargs that effect function takes:

```json
"effects": {
    "gain": { "target_track": "vocals.wav", "amount": 3 },
    "fade_out": { "time": 1500 }
}
```

Drop a new `.py` file into `Effects/` with the same `effect_name` convention to add more
effects — no other code changes needed.

---

## Track JSON schema

Each track folder (created by `udio-add`) holds a `<track name>.json`:

```json
{
    "mix": {
        "ignore": true,
        "source_path": "Track Name 1.zip",
        "bitrate": "192k",
        "output_file": "Track Name 1.mp3",
        "effects": {}
    },
    "tags": { "energy": 0.0, "mood": 0.0, "pop": 0.0, "stars": 0 },
    "export_parameters": { "export": false }
}
```

- `mix` — read by `udio-mix`; `ignore: true` skips the track until you're ready to mix it.
- `tags` — free-form metadata surfaced by `udio-analyze` and copied into the exported
  `.meta.json` by `udio-export`.
- `export_parameters.export` — gates whether `udio-export` picks the track up at all.
