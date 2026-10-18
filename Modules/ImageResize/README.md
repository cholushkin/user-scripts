# ImageResize

Batch-resizes/converts images (including SVG rasterization) from the CLI, the file
manager, or the interactive UI.

## Quick Start (CLI)

```
resize --paths "D:/Art/texture.png;D:/Art/icons" --scale 0.5 --format webp
```

Or directly through the launcher:

```
epy "c:\Apps\user-scripts\Modules\ImageResize\image_resize.py" --paths "D:/Art" --recursive
```

## Interactive Mode

Hold **Left Ctrl** while launching `resize` (or pass `--interactive`) to open the Dear
PyGui UI.

## Parameters

### Input

| Param | Default | Description |
| --- | --- | --- |
| `paths` | `""` | Files or folders, semicolon-separated. Falls back to the Double Commander selection file, then `--cwd`, if empty. |
| `recursive` | `False` | Process directories recursively. |

### Resize

| Param | Default | Description |
| --- | --- | --- |
| `scale` | `0.5` | Scale factor used when `width`/`height` are both `0`. |
| `width` | `0` | Target width (`0` = derive from scale/aspect). |
| `height` | `0` | Target height (`0` = derive from scale/aspect). |
| `keep_aspect` | `True` | Preserve aspect ratio when `width`/`height` are set. |

### Output

| Param | Default | Description |
| --- | --- | --- |
| `output_dir` | `.` | Destination folder. |
| `format` | `jpg` | `jpg`, `webp`, or `png`. SVGs always rasterize to `png`. |
| `quality` | `60` | JPEG/WEBP quality (0-100). |
| `overwrite` | `False` | Overwrite existing output files instead of skipping them. |

### Shared (from `BaseScript`)

`log_level`, `log_file`, `interactive`.

## Supported input formats

`.jpg .jpeg .png .bmp .tiff .webp .svg`

SVG rasterization requires the optional `cairosvg` package (`pip install cairosvg`); if
it's missing, SVG files are skipped with an error instead of crashing the batch.

## Behavior notes

- Existing output files are skipped (and logged as a warning) unless `overwrite` is set.
- `jpg` output coerces `RGBA`/`P` images to `RGB`; `webp` output coerces `P` to `RGBA`.
- When invoked from Double Commander with files selected, those selected files take
  priority over `--paths`.
