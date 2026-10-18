# PhotoshopExport

**Status: planned — no script yet.**

Intended to mirror [`Modules/KritaExport`](../KritaExport/README.md): batch-export
layered `.psd`/`.psb` documents into a structured scene description plus baked images,
driven headlessly from Photoshop (likely via a `.jsx`/UXP plugin instead of Krita's
Python plugin API).

Expected shape once implemented, following the same pattern as `KritaExportScript.py`:

- A `PhotoshopExportScript.py` subclassing `BaseScript`, taking a Photoshop executable
  path, output directory override, and an objects/layer filter.
- A `PhotoshopExportPlugin/` payload installed into Photoshop's scripts/plugins folder,
  analogous to `KritaExportPlugin/`.
- The same `.uscript` project-domain resolution and Double Commander selection-file
  input handling used by `KritaExport`.
