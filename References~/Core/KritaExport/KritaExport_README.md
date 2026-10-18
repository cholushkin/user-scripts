# Krita Layer Export -- Design Documentation

[e] → export
[m] → merge group
[c] → auto crop
[c: l,t,r,b] → auto crop + margins
No [c] → no crop
Multiple [] blocks supported
Everything inside [] treated as command block
Real name = name with all [] removed

------------------------------------------------------------------------

# 1. Overview

The goal of this tool is to export a Krita document into:

-   A structured JSON scene description
-   A set of baked PNG images
-   Preserved layer hierarchy
-   Deterministic file naming

The exporter is engine-agnostic. It does not contain Unity-specific
logic. Unity (or any other engine) is responsible for reconstructing the
hierarchy and applying gameplay semantics.

------------------------------------------------------------------------

# 2. Design Philosophy

## 2.1 Engine-Agnostic Krita Side

The Krita plugin:

-   Exports structure and visuals only
-   Does not define colliders, anchors, gameplay tags, or components
-   Bakes all visual effects into final pixels

All gameplay semantics must be defined on the engine side.

------------------------------------------------------------------------

# 3. Core Architectural Decisions

## 3.1 No Stable Cross-Referencing

-   No persistent UUID per layer
-   No incremental prefab updating
-   Every export is treated as a full rebuild
-   Layer identity is defined purely by hierarchy structure

------------------------------------------------------------------------

## 3.2 Synthetic Root

Exporter always creates a synthetic root node:

``` json
"root": {
  "name": "<DocumentName>",
  "type": "group",
  "children": []
}
```

------------------------------------------------------------------------

## 3.3 Nested JSON Structure

Hierarchy is represented directly as nested JSON.

No parent IDs.\
No path-based references.\
Hierarchy equals identity.

------------------------------------------------------------------------

## 3.4 Flat Image Output

Images are exported into a single directory.

Naming rule:

    Root_Group_Layer.png

Full hierarchy path joined with underscores.

------------------------------------------------------------------------

# 4. Layer Metadata

Metadata key:

    layer_export

Stored as JSON string in node properties.

``` json
{
  "export": true,
  "crop": "auto",
  "merge": false
}
```

------------------------------------------------------------------------

# 5. Export Rules

## 5.1 Export Filtering

-   Only layers with export=true are processed
-   Parent export=false → subtree ignored
-   Visibility does NOT block export

## 5.2 Group Handling

merge = false → preserve hierarchy\
merge = true → bake group to single image

## 5.3 Baking

Automatically baked:

-   Masks
-   Filters
-   Adjustment layers
-   Blend modes
-   Clone layers
-   Opacity

## 5.4 Cropping

crop = "auto" → crop to non-transparent bounds\
crop = "none" → full document bounds

Transparent results are skipped.

------------------------------------------------------------------------

# 6. JSON Schema (v1)

``` json
{
  "version": 1,
  "document": {
    "width": 2048,
    "height": 2048
  },
  "root": {
    "name": "Character",
    "type": "group",
    "children": []
  }
}
```

------------------------------------------------------------------------

# 7. Command-Line Automation (Workaround)

Krita does not reliably support direct Python execution via CLI in many
Windows builds.

Instead, we use an environment-variable-driven auto-export mode.

## 7.1 How It Works

1.  Krita starts normally with a .kra file.

2.  Plugin checks environment variable:

        KRITA_LAYER_EXPORT_AUTO=1

3.  If set:

    -   Wait until document is fully loaded
    -   Export JSON + PNG
    -   Quit Krita automatically

This avoids custom CLI flags (which Qt rejects).

------------------------------------------------------------------------

## 7.2 Example Windows CMD Script

``` cmd
@echo off

set KRITA_LAYER_EXPORT_AUTO=1
set KRITA_LAYER_EXPORT_OUTPUT=D:\output

"C:\Program Files\Krita (x64)in\krita.exe" --nosplash "D:ile.kra"
```

------------------------------------------------------------------------

## 7.3 Behavior

-   No unknown CLI options
-   Works with standard Krita builds
-   Uses Qt event loop synchronization
-   Automatically exits after export

------------------------------------------------------------------------

# 8. File Structure

    pykrita/
        layer_export/
            __init__.py
            ExportCore.py
        layer_export.desktop

------------------------------------------------------------------------

# 9. Limitations

-   No incremental updates
-   No stable layer IDs
-   Static export only
-   GUI briefly opens during automation
-   Not true headless (Qt GUI still initializes)

------------------------------------------------------------------------

# 10. Recommended Production Pipeline

1.  Artist edits .kra
2.  Run export script (CMD or CI system)
3.  Krita auto-exports and quits
4.  Engine importer rebuilds prefab
5.  Deterministic full rebuild each time

------------------------------------------------------------------------

# 11. Future Improvements

-   Metadata editing UI dock
-   Faster crop algorithm
-   Animation export
-   Batch processing
-   Structured logging system

------------------------------------------------------------------------
