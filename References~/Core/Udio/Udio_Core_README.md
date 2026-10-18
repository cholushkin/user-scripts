# Udio (Core Audio Processing Module)

## Overview

**Udio** is the audio processing and track management subsystem inside
ScriptUtils.

It provides a full pipeline for:

-   Adding new tracks
-   Mixing multi-stem audio
-   Applying audio effects
-   Exporting processed tracks to Unity
-   Analyzing track database metadata

The system is modular and configuration-driven, designed for
automation-heavy workflows.

------------------------------------------------------------------------

## Location

    ScriptUtils/Core/Udio/

------------------------------------------------------------------------

# Components Overview

## 1. MixTracks

**Purpose:**\
Processes track JSON configurations, extracts stems from ZIP files,
applies effects, merges audio, and exports final MP3 files.

### Key Features

-   Extracts expected stems (bass, drums, vocals, other)
-   Strict stem validation
-   Dynamic effect loading from Effects folder
-   Overlay-based audio merging
-   Bitrate configuration
-   Per-track override support
-   Ignore flag support

### Primary Use Case

Automated audio production pipeline.

------------------------------------------------------------------------

## 2. ExportTracks

**Purpose:**\
Copies finished MP3 tracks to Unity project and generates simplified
metadata files.

### Key Features

-   Searches track folders recursively
-   Reads JSON configuration
-   Copies MP3 to Unity asset folder
-   Generates `.meta.json` file
-   Adds music configuration reference
-   Respects export flag

### Primary Use Case

Final stage of audio pipeline → Unity integration.

------------------------------------------------------------------------

## 3. AddNewTracks

**Purpose:**\
Organizes raw MP3 + ZIP pairs into structured project folders and
generates default JSON configuration files.

### Key Features

-   Validates MP3/ZIP pairs
-   Creates numbered subfolders
-   Auto-generates JSON config using template
-   Move or copy mode
-   Error-safe file operations

### Primary Use Case

Initial ingestion of newly created tracks.

------------------------------------------------------------------------

## 4. AnalyzeTrackDB

**Purpose:**\
Scans MP3 database and analyzes metadata, duration, size, and
duplicates.

### Key Features

-   Reads JSON metadata (energy, mood, pop, stars)
-   Detects missing JSON files
-   Calculates total duration
-   Estimates storage at different bitrates
-   Detects duplicate files (MD5 + name)

### Primary Use Case

Track library auditing and optimization.

------------------------------------------------------------------------

## 5. Effects System

Located in:

    ScriptUtils/Core/Udio/Effects/

Effects are dynamically loaded Python modules.

### Built-in Effects

-   **gain** -- Volume adjustment
-   **fade_in / fade_out**
-   **cut_beginning / cut_end**
-   **reverb** (via Sox external tool)

### Architecture

Each effect file exposes:

``` python
effect_name = {
    "effect_identifier": function_reference
}
```

MixTracks dynamically loads these at runtime.

------------------------------------------------------------------------

# JSON Track Structure

Each track uses a configuration file like:

``` json
{
  "mix": { ... },
  "tags": { ... },
  "export_parameters": { ... }
}
```

### Sections

-   `mix` -- Audio processing configuration
-   `tags` -- Metadata values
-   `export_parameters` -- Controls Unity export

------------------------------------------------------------------------

# Typical Workflow

1.  Add raw files → `AddNewTracks`
2.  Mix stems → `MixTracks`
3.  Analyze database → `AnalyzeTrackDB`
4.  Export to Unity → `ExportTracks`

------------------------------------------------------------------------

# Configuration

Uses global settings from:

    ScriptUtils/Config/default_config.json
    ScriptUtils/Config/user_config.json

Respects:

-   log_level
-   unity_project_root

------------------------------------------------------------------------

# Requirements

-   Python
-   pydub
-   mutagen (for analysis)
-   Sox (for reverb effect)
-   FFmpeg (required by pydub)

------------------------------------------------------------------------

# Design Philosophy

-   Configuration-driven
-   Modular effects system
-   Safe file handling
-   Clear logging structure
-   Unity pipeline integration

------------------------------------------------------------------------

Generated on: 2026-02-18 22:34:58
