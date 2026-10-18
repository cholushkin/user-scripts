# BackupUtil (Core Module)

## Overview

**BackupUtil** is a core utility module designed to create structured
ZIP backups of selected project folders.\
It is part of the `ScriptUtils/Core` package and is intended to be
reused across multiple Unity or development projects.

The tool:

-   Creates compressed ZIP archives
-   Supports exclude patterns (glob-style)
-   Automatically appends date to filename
-   Prevents overwriting existing backups
-   Logs progress using the internal LogManager

------------------------------------------------------------------------

## Location

    ScriptUtils/Core/BackupUtil/BackupUtil.py

------------------------------------------------------------------------

## Features

-   ZIP compression using `ZIP_DEFLATED`
-   Automatic `{DATE}` replacement in destination filename
-   Pattern-based file exclusion (`fnmatch`)
-   Intelligent duplicate-name handling
-   Execution time reporting
-   Configurable logging level via `ConfigManager`

------------------------------------------------------------------------

## Initialization

``` python
BackupUtil(destination_path, folders, excludes=None)
```

### Parameters

  -----------------------------------------------------------------------
  Parameter                   Type          Description
  --------------------------- ------------- -----------------------------
  `destination_path`          str           Output ZIP path (supports
                                            `{DATE}` placeholder)

  `folders`                   list\[str\]   List of folders (relative to
                                            project root) to include

  `excludes`                  list\[str\]   Optional glob patterns to
                                            exclude files
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## Example Usage

``` python
from Core.BackupUtil.BackupUtil import BackupUtil

backup = BackupUtil(
    destination_path="Backups/project_backup_{DATE}.zip",
    folders=["Assets", "ProjectSettings"],
    excludes=["*.tmp", "*.log", "Library/*"]
)

backup.run()
```

------------------------------------------------------------------------

## How It Works

1.  Resolves project root automatically.
2.  Replaces `{DATE}` in filename with current date (YYYY-MM-DD).
3.  Scans selected folders recursively.
4.  Skips files matching exclude patterns.
5.  Creates ZIP archive.
6.  Prints summary (file count + duration).

------------------------------------------------------------------------

## Logging

Uses `LogManager` and respects global `log_level` from:

    ScriptUtils/Config/default_config.json
    ScriptUtils/Config/user_config.json

Supported log levels:

-   `important`
-   `normal`
-   `verbose`
-   `disabled`

------------------------------------------------------------------------

## When to Use

Use BackupUtil when you need:

-   Pre-build backups
-   Automated nightly project snapshots
-   Source + config archiving
-   Safe manual backups before major refactors

------------------------------------------------------------------------

## Notes

-   Paths are always interpreted relative to the project root.
-   Existing backup files will automatically get numbered suffixes.
-   Exclusion patterns use standard glob syntax.

------------------------------------------------------------------------

Generated on: 2026-02-18 22:25:28
