# Blender

Batch-exports objects (with their full child hierarchy) from a `.blend` file into FBX,
by driving Blender headlessly, with optional Unity axis conversion. Ported from the old
`ScriptUtils/Core/Blender` (`BlenderExport.py` + `ExportFbxObject.py`), mirroring the same
driver/payload split used by [`Modules/KritaExport`](../KritaExport/README.md).

## Quick Start (CLI)

```
epy "c:\Apps\user-scripts\Modules\Blender\BlenderExportScript.py" --blend_file "D:/Art/Scene.blend" --objects "Character;Environment"
```

Typical usage is from Double Commander: select (or `cd` into the folder of) a `.blend`
file and run the script — see **Input resolution**.

## Interactive Mode

Hold **Left Ctrl** while launching the script (or pass `--interactive`) to open the Dear
PyGui UI.

## Parameters

### Export Settings

| Param | Default | Description |
| --- | --- | --- |
| `blender_exe` | `C:\Program Files\Blender Foundation\Blender\blender.exe` | Path to the Blender executable. |
| `blend_file` | `""` | Path to the `.blend` file. Blank = resolved from the Double Commander selection or `--cwd` if it points at a `.blend` file. |
| `export_dir` | `""` | Override export directory. Blank = resolved via the discovered `.uscript` project's asset folder, else `--cwd`, else the `.blend` file's own folder. |
| `unity_axis_conversion` | `True` | On: forward=`-Z`, up=`Y` (matches Unity). Off: forward=`Y`, up=`Z` (Blender default). |
| `objects` | `""` | Object names to export, each with its full child hierarchy, semicolon-separated. One FBX file per object. |

### Shared (from `BaseScript`)

`log_level`, `log_file`, `interactive`.

## How it works

1. **BlenderExportScript.py** (this repo's `BaseScript` tool) resolves the `.blend` file,
   export directory and object list, then launches:
   ```
   blender --background --python ExportFbxObject.py -- <blend_file> <export_dir> <true|false> <objects...>
   ```
2. **ExportFbxObject.py** runs *inside* Blender's own Python (`bpy`), which is only
   available at Blender runtime — it cannot import this repo's `Shared` framework, so it
   stays a standalone script, same as `Modules/KritaExport/KritaExportPlugin/`. For each
   requested object it:
   - Opens the `.blend` file.
   - Finds the object by name (first match if duplicates exist).
   - Unhides it, its full child hierarchy, and all of its parents (so hidden setups still
     export correctly).
   - Selects the object + children and exports an FBX (`MESH`, `ARMATURE`, `EMPTY` types;
     custom properties preserved) to `<export_dir>/<object_name>.fbx`.

## Notes

- Blender's GUI briefly initializes during each run even in `--background` mode — this is
  not a true headless process.
- Each object in `objects` produces a separate FBX file; the export directory is created
  automatically if missing.
