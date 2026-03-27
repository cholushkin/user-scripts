# Script Pipeline System

A lightweight, parameter-driven scripting framework designed for use with Double Commander, Total Commander, or standalone CLI workflows.

## Overview

This system provides a unified way to build reusable scripts that can run in three modes:
- **Default mode**: executes with smart defaults (fast execution)
- **Interactive mode (TUI)**: powered by Textual for editing parameters
- **CLI mode**: full control via command-line arguments

## Key Features

- **Parameter-driven design**
  - All scripts define parameters using a structured `Param` system
  - Supports types, defaults, hints, and validation

- **Smart defaults**
  - Scripts can run instantly without user input
  - Defaults can adapt based on context (e.g. selected files)

- **Interactive Textual UI**
  - Clean terminal-based interface (no external windows)
  - Edit parameters in a form-like layout
  - Keyboard-first navigation
  - Dynamic visibility of fields

- **Recent parameters**
  - Quickly reuse recently executed parameter sets
  - No full preset system (yet), but designed to support it later

- **Preview support**
  - Scripts can show expected results before execution
  - Ideal for file operations (rename, convert, resize)

- **Shared core**
  - Common logic lives in `BaseScript` and `ScriptEnv`
  - UI (CLI/TUI) is separated from execution logic

## Architecture

```
/shared
  BaseScript.py
  ScriptEnv.py
  Param.py

/ui
  cli.py
  textual_ui.py

/scripts
  resize_images.py
  rename_files.py
```

## Philosophy

- Fast by default
- Minimal user input
- Keyboard-first workflows
- Works inside file managers
- UI is optional, not required

## Future Extensions

- Presets system
- Script composition (pipelines)
- Plugin system

---

This project aims to turn simple scripts into a consistent, reusable, and user-friendly execution framework.
