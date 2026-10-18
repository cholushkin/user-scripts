# How To Add New Core Modules to ScriptUtils

This document describes the conventions and structure required when
adding a new Python module to the `ScriptUtils/Core` directory.

The goal is to maintain consistency, configurability, and predictable
logging behavior across all modules.

------------------------------------------------------------------------

# 1. Directory Structure

All reusable logic must live inside:

    ScriptUtils/Core/<YourModuleName>/

Example:

    ScriptUtils/Core/MyNewModule/
        MyNewModule.py
        MyNewModule_README.md

Rules:

-   Module folder name = PascalCase
-   Main file name = same as folder name
-   Module must not assume execution from its own directory
-   All paths must resolve relative to project root

------------------------------------------------------------------------

# 2. Project Root Convention

Every module must resolve project root dynamically using:

``` python
self.project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
```

Never hardcode absolute paths.

All user-provided paths must be interpreted relative to `UserProject`
root.

------------------------------------------------------------------------

# 3. Configuration (MANDATORY)

All modules must use `ConfigManager`.

Import:

``` python
from Core.ConfigManager import ConfigManager
```

Initialize inside constructor:

``` python
self.config_manager = ConfigManager()
self.config = self.config_manager.load_config()
```

Access configuration values via:

``` python
value = self.config.get("some_key")
```

Never read JSON config files directly in a module.

Configuration precedence:

1.  default_config.json
2.  user_config.json (overrides default)

------------------------------------------------------------------------

# 4. Logging (MANDATORY)

All modules must use `LogManager`.

Import:

``` python
from Core.LogManager import LogManager
```

Initialize after loading config:

``` python
self.log_manager = LogManager(self.config.get("log_level", "normal"))
```

Optional override pattern:

``` python
if custom_log_level is not None:
    self.log_manager.globalLogLevel = custom_log_level
```

Use logging like:

``` python
self.log_manager.log("important", "Critical message")
self.log_manager.log("normal", "Standard message")
self.log_manager.log("verbose", "Detailed message")
```

Never use raw `print()` for operational logs.

Allowed log levels:

-   important
-   normal
-   verbose
-   disabled

------------------------------------------------------------------------

# 5. Constructor Pattern

Recommended constructor structure:

``` python
class MyNewModule:

    def __init__(self, some_parameter, log_level=None):

        self.project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )

        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

        self.log_manager = LogManager(self.config.get("log_level", "normal"))

        if log_level is not None:
            self.log_manager.globalLogLevel = log_level

        self.some_parameter = some_parameter
```

------------------------------------------------------------------------

# 6. Public Entry Point

Each module should expose a `run()` method.

Example:

``` python
def run(self):
    self.log_manager.log("important", "Starting MyNewModule...")
    # Do work here
```

UserScripts should only call `.run()`.

------------------------------------------------------------------------

# 7. Path Handling Rules

-   Always use `os.path.join`
-   Always resolve absolute paths from `self.project_root`
-   Never assume working directory
-   Never use relative filesystem operations without root resolution

Example:

``` python
absolute_path = os.path.join(self.project_root, relative_path)
```

------------------------------------------------------------------------

# 8. Error Handling Rules

-   Catch predictable exceptions
-   Log failures using `important` level
-   Do not silently fail
-   Avoid crashing entire script unless truly fatal

Example:

``` python
try:
    do_something()
except Exception as e:
    self.log_manager.log("important", f"Error: {e}")
```

------------------------------------------------------------------------

# 9. Optional Patterns

Depending on module type:

• If interacting with external tools → use `subprocess.run()`\
• If scanning files → use `os.walk()`\
• If generating output → ensure directory exists using
`os.makedirs(..., exist_ok=True)`

------------------------------------------------------------------------

# 10. Documentation Requirement

Every module must include:

    <ModuleName>_README.md

The README must include:

-   Overview
-   Purpose
-   Configuration requirements
-   Example usage
-   Dependencies
-   Notes

------------------------------------------------------------------------

# 11. What NOT To Do

Do NOT:

-   Hardcode paths
-   Hardcode configuration values
-   Use print() instead of LogManager
-   Access config JSON files directly
-   Assume execution from specific working directory
-   Mix user-entry logic with core logic

Core = reusable logic only.

------------------------------------------------------------------------

# 12. Minimal Template Example

``` python
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from Core.ConfigManager import ConfigManager
from Core.LogManager import LogManager


class MyNewModule:

    def __init__(self, log_level=None):

        self.project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )

        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

        self.log_manager = LogManager(self.config.get("log_level", "normal"))

        if log_level is not None:
            self.log_manager.globalLogLevel = log_level

    def run(self):
        self.log_manager.log("important", "MyNewModule started")
```

------------------------------------------------------------------------

Generated on: 2026-02-18 22:48:21
