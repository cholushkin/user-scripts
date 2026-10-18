# KritaExport

Batch-exports layered `.kra` documents into a structured JSON scene description plus
baked PNG images, by driving Krita headlessly through a bundled Python plugin
(`KritaExportPlugin`). Designed to be triggered from a file manager with one or more
`.kra` files selected.

## Quick Start (CLI)

```
epy "c:\Apps\user-scripts\Modules\KritaExport\KritaExportScript.py" --cwd "D:/Art/character.kra"
```

Typical real-world usage is from Double Commander: select one or more `.kra` files and
run the script — it reads the selection file automatically (see **Input resolution**).

## Interactive Mode

Hold **Left Ctrl** while launching the script (or pass `--interactive`) to open the Dear
PyGui UI.

## Parameters

### Export Settings

| Param | Default | Description |
| --- | --- | --- |
| `krita_exe` | `C:\Program Files\Krita (x64)\bin\krita.exe` | Path to the Krita executable. |
| `output_dir` | `""` | Override export output directory (optional; otherwise the plugin decides). |
| `objects` | `""` | Comma-separated filter — only export layers/objects matching these names. |
| `force_update` | `False` | Force-reinstall the bundled Krita plugin even if versions already match. |

### Shared (from `BaseScript`)

`log_level`, `log_file`, `interactive`.

## Input resolution

Files to process are resolved in this order:

1. **Double Commander selection** — if `--selected` points at a selection file, every
   line in it is treated as a path (relative entries are resolved against `--cwd`).
2. **`--cwd`** — used as a single input path if nothing was selected.

Only paths ending in `.kra` are kept; everything else is ignored.

## What happens on export

1. **Plugin sync** — on first run (or when `force_update` is set, or the bundled
   plugin version is newer) the script copies `KritaExportPlugin/` into Krita's
   `%APPDATA%\krita\pykrita\layer_export` folder and enables it in `kritarc`.
2. **Headless run** — for each `.kra` file, Krita is launched with
   `--nosplash <file>` and a set of `KRITA_LAYER_EXPORT_*` environment variables
   (auto-export flag, output override, objects filter, project root/asset folder from
   the discovered `.uscript` domain, log directory). The plugin exports JSON + PNGs
   and quits Krita automatically — see **How It Works** below.
3. **Log pipe** — Krita's own `krita-export.log` (written to the current working
   directory) is read back and piped into this script's log under a `[Krita]` prefix.

If a sibling `<document>.json` file exists next to the `.kra` file, it's passed to the
plugin as additional export configuration.

## How It Works (Krita side)

Krita doesn't reliably support headless CLI execution on Windows, so the plugin uses an
environment-variable-driven auto-export mode instead of custom CLI flags:

1. Krita starts normally with the `.kra` file open.
2. The plugin checks for `KRITA_LAYER_EXPORT_AUTO=1`.
3. If set, it waits for the document to finish loading, exports JSON + PNG, then quits
   Krita automatically.

## Design notes

- **Export rules** (layer metadata driven): only layers tagged `export: true` are
  processed; a parent tagged `export: false` skips its whole subtree. Visibility does
  **not** gate export. `merge: true` bakes a group to a single image; `merge: false`
  preserves the hierarchy. `crop: "auto"` crops each exported image to its
  non-transparent bounds; `crop: "none"` keeps the full document bounds. Metadata is
  stored per-layer under a `layer_export` property, e.g. `{"export": true, "crop": "auto", "merge": false}`.
- **Output shape**: a synthetic root node wraps the hierarchy; images are flattened into
  a single output directory, named by joining the full hierarchy path with underscores
  (`Root_Group_Layer.png`). There are no stable per-layer IDs — every export is a full
  rebuild, not an incremental update.
- **Engine-agnostic**: the plugin only exports structure + baked visuals (masks,
  filters, adjustment layers, blend modes, clone layers, opacity are all baked in).
  Gameplay semantics (colliders, anchors, tags) are the importing engine's
  responsibility, not this tool's.

## Limitations

- Krita's GUI briefly flashes open during each export — it is not truly headless.
- No incremental export: every run is a full rebuild of the document's export output,
  and there are no stable cross-references between runs.
