# Script Pipeline System

A lightweight, parameter-driven scripting framework designed for use
with Double Commander, Total Commander, or standalone CLI workflows.

## Overview

This system provides a unified way to build reusable scripts that can
run in three modes:

-   **Default mode**: executes with smart defaults (fast execution)
-   **CLI mode**: full control via command-line arguments
-   **Interactive mode (TUI)** *(planned)*: powered by Textual

------------------------------------------------------------------------

## Key Concepts

### 1. Single Source of Truth (Param)

All script behavior is defined through `Param`:

-   Name → CLI argument
-   Type → parsing + validation
-   Default → initial value

``` python
Param("path", str, ".")
Param("dirs_only", bool, False)
```

From this, the system automatically generates:

``` bash
--path D:\temp
--dirs_only
--no-dirs_only
```

------------------------------------------------------------------------

### 2. Defaults (User Editable)

Each script defines a `DEFAULTS` dictionary at the top:

``` python
DEFAULTS = {
    "path": ".",
    "dirs_only": False,
    "log_level": 20,
    "log_file": "Tree.log",
}
```

Purpose: - Quick manual tweaking - No need to touch shared code

------------------------------------------------------------------------

### 3. Execution Flow

Final parameter values are resolved in this order:

    DEFAULTS → CLI args → External context (Double Commander)

------------------------------------------------------------------------

### 4. Logging System

Built-in structured logging:

``` python
self.log_debug("debug")
self.log_info("info")
self.log_warn("warning")
self.log_error("error")
```

Features: - Log levels (10--40) - Configurable prefixes - Optional file
output - Clean output (no prefix for INFO)

------------------------------------------------------------------------

### 5. CLI Support (argparse)

CLI is automatically generated from `Param`.

Supported: - `--key value` - `--key=value` - boolean flags (`--flag`,
`--no-flag`) - `--help`

Example:

``` bash
python print_tree.py --path D:\temp --dirs_only --log_level 10
```

------------------------------------------------------------------------

### 6. Double Commander Integration

Scripts can be launched like:

``` bash
print_tree.py --cwd "%p" --selected %F
```

The system captures these into:

``` python
self.context.extra = {
    "cwd": "...",
    "selected": "..."
}
```

Important:

-   `--cwd` may contain a file path → scripts must normalize it
-   `--selected` points to a file list (future feature)

------------------------------------------------------------------------

### 7. Script Responsibility

**BaseScript** - parses CLI - collects external context - handles
logging

**Script** - interprets context - defines behavior

Example:

``` python
if os.path.isfile(root):
    root = os.path.dirname(root)
```

------------------------------------------------------------------------

## Architecture

    /Shared
      base_script.py
      context.py
      param.py

    /FileSystem
      print_tree.py

------------------------------------------------------------------------

## Philosophy

-   Fast by default
-   Minimal boilerplate
-   One definition (Param) → multiple interfaces (CLI, default mode,interactive mode, validation, context integration)
-   Works inside file managers
-   Clear separation of concerns

------------------------------------------------------------------------

## Current Features

-   Param-driven system
-   Script-level defaults
-   CLI auto-generation
-   Logging system
-   Double Commander context support
-   Clean output formatting

------------------------------------------------------------------------

## Next Steps

-   Interactive TUI (Textual)
-   Selected files parsing
-   Presets / history
-   Script discovery system

------------------------------------------------------------------------

This project aims to turn simple scripts into a consistent, reusable,
and user-friendly execution framework.
