
# Script Pipeline System

A lightweight, parameter-driven scripting framework designed for use
with Double Commander, Total Commander, or standalone CLI workflows.

## Overview

This system provides a unified way to build reusable scripts that can
run in three modes:

- **Default mode**: executes with smart defaults (fast execution)
- **CLI mode**: full control via command-line arguments
- **Interactive mode (GUI)**: powered by Dear PyGui

------------------------------------------------------------------------

## Key Concepts

### 1. Single Source of Truth (Param)

All script behavior is defined through `Param`:

- Name → CLI argument
- Type → parsing + validation
- Default → initial value
- Hints → optional UI/CLI suggestions

```python
Param("path", str, ".")
Param("dirs_only", bool, False)
```

Automatically generates:

```bash
--path D:\temp
--dirs_only
--no-dirs_only
```

------------------------------------------------------------------------

### 2. Defaults (User Editable)

Each script defines a `DEFAULTS` dictionary:

```python
DEFAULTS = {
    "path": ".",
    "dirs_only": False,
    "log_level": 20,
}
```

Purpose:
- Quick manual tweaking
- No need to touch shared code

------------------------------------------------------------------------

### 3. Execution Flow

Final parameter values are resolved in this order:

DEFAULTS → CLI args → Interactive UI → External context

------------------------------------------------------------------------

### 4. Interactive GUI Mode

Powered by **Dear PyGui**.

Features:
- Auto-generated UI from `Param`
- Dropdowns via `hints`
- Boolean → checkbox
- Int → numeric input
- String → text input
- Help section with defaults
- External help loaded from `how_it_works.txt`

Example hint usage:

```python
Param(
    "log_level",
    int,
    20,
    hints={
        "10 - DEBUG": 10,
        "20 - INFO": 20,
        "30 - WARN": 30,
        "40 - ERROR": 40,
    }
)
```

UI shows:
```
10 - DEBUG
20 - INFO
```

Internal value remains numeric.

------------------------------------------------------------------------

### 5. Logging System

```python
self.log_debug("debug")
self.log_info("info")
self.log_warn("warning")
self.log_error("error")
```

Features:
- Log levels (10–40)
- Optional file output
- Clean formatting

------------------------------------------------------------------------

### 6. CLI Support

Auto-generated via argparse:

Supported:
- `--key value`
- `--key=value`
- `--flag` / `--no-flag`

Example:

```bash
python print_tree.py --path D:\temp --dirs_only --log_level 10
```

------------------------------------------------------------------------

### 7. Double Commander Integration

```bash
print_tree.py --cwd "%p" --selected %F
```

Captured as:

```python
self.context.extra = {
    "cwd": "...",
    "selected": "..."
}
```

------------------------------------------------------------------------

## Architecture

```
/Shared
  base_script.py
  context.py
  param.py
  interactive_app.py

/FileSystem
  print_tree.py
```

------------------------------------------------------------------------

## Philosophy

- Fast by default
- Minimal boilerplate
- One definition → multiple interfaces
- Clean separation of concerns
- Works in GUI + CLI environments

------------------------------------------------------------------------

## Current Features

- Param-driven system
- CLI auto-generation
- Interactive GUI (Dear PyGui)
- Logging system
- External help support
- Context integration

------------------------------------------------------------------------

## Next Steps

- Presets system
- Collapsible UI sections
- File pickers for paths
- History / last used params
- Script discovery

------------------------------------------------------------------------

This project aims to turn simple scripts into a consistent,
reusable, and user-friendly execution framework.
