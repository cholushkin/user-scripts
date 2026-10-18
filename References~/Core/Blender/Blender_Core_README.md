# Blender Export Utilities (Core Module)

## Overview

The **Blender Export** module provides automation tools for exporting
objects from `.blend` files into FBX format, primarily for Unity
workflows.

It enables:

-   Headless Blender execution
-   Selective object export
-   Automatic Unity axis conversion
-   Export of object hierarchies (including children)
-   Integration with project configuration

This module is designed to run Blender via command line using a
configured Blender executable.

------------------------------------------------------------------------

## Location

    ScriptUtils/Core/Blender/
    ├── BlenderExport.py
    └── ExportFbxObject.py

------------------------------------------------------------------------

## Components

### 1. BlenderExport.py

Responsible for:

-   Reading configuration (Blender executable path, Unity root)
-   Building the Blender CLI command
-   Running Blender in background mode
-   Passing export parameters
-   Logging execution results

------------------------------------------------------------------------

### 2. ExportFbxObject.py

Executed *inside Blender*.

Responsible for:

-   Opening `.blend` file
-   Finding target object
-   Unhiding object + full hierarchy
-   Selecting object and children
-   Exporting to FBX format
-   Optional Unity axis conversion

------------------------------------------------------------------------

## Configuration

Uses settings from:

    ScriptUtils/Config/default_config.json
    ScriptUtils/Config/user_config.json

Required configuration keys:

  Key                    Description
  ---------------------- -------------------------------------
  `blender_executable`   Path to Blender executable
  `unity_project_root`   Relative path to Unity project root
  `log_level`            Logging verbosity

------------------------------------------------------------------------

## Example Usage

``` python
from Core.Blender.BlenderExport import run_blender_export

run_blender_export(
    blend_file="Art/MyScene.blend",
    export_directory="Assets/Models",
    unity_axis_conversion=True,
    objects_to_export=["Character", "Environment"]
)
```

------------------------------------------------------------------------

## How It Works

1.  Resolves project root.
2.  Builds absolute paths.
3.  Constructs Blender CLI command:
    -   `--background`
    -   `--python ExportFbxObject.py`
    -   custom arguments after `--`
4.  Blender opens file.
5.  Target object is located.
6.  Object + children are selected.
7.  FBX export is executed.
8.  Logs success or failure.

------------------------------------------------------------------------

## Unity Axis Conversion

When enabled:

-   Forward axis: `-Z`
-   Up axis: `Y`

When disabled:

-   Forward axis: `Y`
-   Up axis: `Z`

This ensures correct orientation inside Unity.

------------------------------------------------------------------------

## Supported Object Types

Exports:

-   MESH
-   ARMATURE
-   EMPTY

Custom properties are preserved.

------------------------------------------------------------------------

## Use Cases

-   Automated asset pipeline
-   CI/CD asset builds
-   Batch exporting multiple objects
-   Pre-build model processing
-   Multi-project asset reuse

------------------------------------------------------------------------

## Notes

-   Blender must be installed and accessible via configured path.
-   Script runs in headless mode (no UI).
-   Output directory is created automatically if missing.
-   Each object export generates a separate FBX file.

------------------------------------------------------------------------

Generated on: 2026-02-18 22:30:05
