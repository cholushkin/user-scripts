![project logo](doc-assets/repository-open-graph-cover.png)

ScriptUtils package is helper library that contains the scripts used across the Unity projects. These are primarily Python and Windows batch (.cmd/.bat) files designed to automate and streamline development workflows.
Switch to `UserScriptsExamples` branch for a user scripts examples taken from the real project.


## 📁 Structure

```
UserProject/ 
├─UserScripts/    
└─ScriptUtils/ 
  ├── Core/       
  └── Config/
```

## 📂 Folder Descriptions

*Core/* 
Contains the core logic and implementation of helper utilities. These modules are not intended to be executed directly but are used as building blocks for scripts in the Scripts/ folder.

*UserScripts/*
Contains user-executable scripts. These typically serve as entry points and are composed by combining and calling logic from the Core/ directory. Each script solves a specific task like project setup, builds, cleaning temporary files, importing assets to Unity, etc. This folder is under source control of root project.

*Config/*
Stores user- or machine-specific settings and environment variables. Useful for maintaining local configuration without affecting shared scripts.

## Folder Usage Recap
✅ UserScripts - Real, production-ready entry point scripts (under source control) located on the same level as ScriptUtils.
📌 All paths in scripts should be interpreted relative to: UserProject folder (example: d:\projects\dev\UserProject). This is considred as a root folder of the project.


## Utilities
- 🎵 Udio -- Mixes audio stems, applies effects (gain, fade, reverb, cut), exports tracks, analyzes MP3 database; ([README](Core/Udio/Udio_Core_README.md))
- 🧩 Blender Tools -- Exports FBX objects via command line; ([README](Core/Blender/Blender_Core_README.md))
- 📦 BackupUtil -- Creates ZIP backups with exclude rules; ([README](Core/BackupUtil/BackupUtil_README.md))
- 🔗 GitSubmoduleManager -- Adds/removes/updates git submodules; ([README](Core/GitSubmoduleManager/GitSubmoduleManager_README.md))
- 📝 PromptContextCollector -- Collects project files and builds a structured prompt file; ([README](Core/PromptContextCollector/PromptContextCollector_README.md))
