# Emojis

Prints a grid of Unicode emoji characters to the terminal (or log) — a quick cheat
sheet for copy-pasting emoji without leaving the keyboard.

## Quick Start (CLI)

```
emojis --group faces --columns 20
```

Or directly through the launcher:

```
epy "c:\Apps\user-scripts\Modules\Emojis\emojis_all.py" --group all
```

## Interactive Mode

Hold **Left Ctrl** while launching `emojis` (or pass `--interactive`) to open the Dear
PyGui UI.

## Parameters

### Display

| Param | Default | Description |
| --- | --- | --- |
| `group` | `all` | Which emoji range to print. See **Groups** below. |
| `columns` | `16` | Emojis per row. |
| `spacing` | `1` | Number of spaces between emojis in a row. |
| `max_count` | `0` | Stop after printing this many emojis (`0` = unlimited). |
| `show_codepoint` | `False` | Print each emoji's hex codepoint next to it, e.g. `😀(0x1f600)`. |

### Shared (from `BaseScript`)

`log_level`, `log_file`, `interactive`.

## Groups

| Group | Unicode ranges |
| --- | --- |
| `faces` | `1F600`–`1F64F` |
| `symbols` | `2600`–`26FF`, `2700`–`27BF` |
| `transport` | `1F680`–`1F6FF` |
| `shapes` | `1F780`–`1F7FF` |
| `extended` | `1F900`–`1F9FF`, `1FA00`–`1FAFF` |
| `all` | all of the above, plus `1F300`–`1F5FF`, `1F700`–`1F77F`, `1F800`–`1F8FF`, `1FB00`–`1FBFF` |

Some codepoints in a range have no assigned glyph in a given font/terminal and will
render as a blank or placeholder box — this is a terminal/font limitation, not a bug.
