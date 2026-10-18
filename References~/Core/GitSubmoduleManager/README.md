# GitSubmoduleManager (Core Module)

## Overview

**GitSubmoduleManager** is a core utility module that simplifies the
management of Git submodules within a project.

It includes advanced synchronization features that allow you to:

-   Update all submodules to latest remote commits
-   Fix detached HEAD states automatically
-   Ensure submodules are on proper branches
-   Stage updated submodule pointers for commit

------------------------------------------------------------------------

## 🔥 Submodules: The Core Problem (Short Explanation)

Git submodules **do NOT track branches by default**.

Instead, the main repository stores a **specific commit hash** for each
submodule.

That means:

-   Your repository says: *"use this submodule at commit X"*
-   Even if newer commits exist → Git will **NOT update automatically**

### Default Git Philosophy

Git submodules are designed for:

-   ✅ Reproducibility (same exact versions every time)
-   ✅ Deterministic builds
-   ❌ NOT automatic dependency updates

So commands like:

    git submodule update

Will:

> Checkout the exact recorded commit --- NOT the latest version

------------------------------------------------------------------------

## 🚨 Why This Becomes a Problem

Typical situation:

1.  Submodule repository receives new commits
2.  You update submodules
3.  Nothing changes

Reason:

> The main repository still points to an older commit

This behavior is consistent across all Git clients and tools.

------------------------------------------------------------------------

## ✅ Solution Provided by This Module

The method:

### `force_update_all_submodules()`

Performs:

1.  Sync submodules
2.  Initialize if needed
3.  Fetch latest commits
4.  Detect default branch (main/master)
5.  Exit detached HEAD state
6.  Pull latest changes
7.  Stage updated pointers in root repository

------------------------------------------------------------------------

## ✅ Recommended Workflow

``` python
manager = GitSubmoduleManager()
manager.force_update_all_submodules()
```

Then:

    git commit -m "Update submodules"

Result:

-   Submodules are updated to latest versions
-   Repository now points to new commits
-   Changes are visible and ready to commit

------------------------------------------------------------------------

## Features

-   Automatic Git repository root detection
-   Safe Git command execution
-   Add / remove / update submodules
-   **Force update all submodules to latest**
-   Automatic branch detection
-   Detached HEAD recovery
-   Automatic staging of submodule changes
-   Integrated logging

------------------------------------------------------------------------

## Notes

-   This approach makes submodules behave like **live dependencies**
-   Best suited for:
    -   Internal libraries
    -   Multi-repository architectures

⚠️ For strict version control (e.g. releases), manual pinning is still
recommended.

------------------------------------------------------------------------

Generated on: 2026-03-17
