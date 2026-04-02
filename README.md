# Script Pipeline System

Designed to be used together with **OFM** as a lightweight way to run
scripts like built-in tools.

------------------------------------------------------------------------

## Environments (Backends)

Scripts run through `epy.bat`, which can use different backends:

-   **conda** (current default)
-   **micromamba**
-   **default** (system Python)

You can configure backend in `epy.bat`.

------------------------------------------------------------------------

## Running scripts

Main entry point:

    epy script.py

------------------------------------------------------------------------

## Ways to run

### 1. CLI (default)

Run with arguments. Uses default values if not provided.

    epy script.py --param value

------------------------------------------------------------------------

### 2. Aliases

Wrap scripts as commands using `.cmd` files and PATH.

    tree

------------------------------------------------------------------------

### 3. Interactive mode

Hold **Left Ctrl** while running to open UI.

Features: - Edit parameters before execution - Presets (saved per
script) - Embedded log viewer - Separate interactive log file:
`<script>.im_mode.log`

------------------------------------------------------------------------

### 4. From OFM panel

Scripts can be triggered directly from OFM using current directory or
selection.

------------------------------------------------------------------------

## Logging

-   **Interactive mode logs** → `<script>.im_mode.log`
-   **Base script logs** → current working directory (via `log_file`
    param)

------------------------------------------------------------------------

## Interactive mode notes

-   Defaults come from the script (`DEFAULTS`)
-   CLI arguments override defaults
-   UI overrides everything before execution
-   Presets are stored next to script: `<script>.presets.json`

------------------------------------------------------------------------

## Philosophy

-   Scripts behave like CLI tools
-   No global dependencies
-   Minimal setup
-   Same script works:
    -   CLI
    -   Interactive UI
    -   OFM integration
