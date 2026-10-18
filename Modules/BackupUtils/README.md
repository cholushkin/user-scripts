# BackupUtils

Creates a compressed ZIP backup of selected project folders, with glob-based exclusions
and automatic collision-safe naming. Ported from the old `ScriptUtils/Core/BackupUtil`.

## Quick Start (CLI)

```
backup --folders "Assets;ProjectSettings" --destination_path "Backups/project_{DATE}.zip"
```

Or directly through the launcher:

```
epy "c:\Apps\user-scripts\Modules\BackupUtils\BackupScript.py" --folders "Assets"
```

## Interactive Mode

Hold **Left Ctrl** while launching `backup` (or pass `--interactive`) to open the Dear
PyGui UI.

## Parameters

### Backup

| Param | Default | Description |
| --- | --- | --- |
| `root` | `""` | Optional override for the root all other paths are relative to. Blank = the discovered `.uscript` project root (see **Path resolution**), else the current working directory. |
| `folders` | `""` | Folders to include, relative to the resolved root (semicolon-separated). |
| `destination_path` | `Backups/project_backup_{DATE}.zip` | Output `.zip` path, relative to the resolved root. `{DATE}` is replaced with today's date (`YYYY-MM-DD`). |
| `excludes` | `*.tmp;*.log;Library/*;__pycache__/*` | Glob patterns excluded from the archive (semicolon-separated), matched against each file's path relative to the resolved root. |

### Shared (from `BaseScript`)

`log_level`, `log_file`, `interactive`.

## Path resolution

If `root` is blank, the script walks up from `--cwd`/`--selected` (or the current working
directory) looking for a `.uscript` project domain, the same discovery
`Modules/KritaExport` and the interactive UI already use. If one is found, its root
becomes the backup root; otherwise the current working directory is used. This replaces
the old global `unity_project_root` config key — set `root` explicitly, or save it in a
local preset inside a project's `.uscript` folder, to pin it per project.

## Behavior notes

- If the destination zip already exists, a numbered suffix is appended instead of
  overwriting (`backup (2).zip`, `backup (3).zip`, ...).
- Missing source folders are logged as a warning and skipped, not fatal.
- Compression uses `ZIP_DEFLATED`. A summary (file count + duration) is printed at the end.
