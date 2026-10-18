# PromptContextCollector (Core Module)

## Overview

**PromptContextCollector** is a core utility module that aggregates
selected project files into a single structured output file for AI
prompts or documentation generation.

It is designed to:

-   Collect files from multiple directories
-   Filter files using include/exclude patterns
-   Embed full file contents into a single output document
-   Inject template-based prompt content
-   Produce a ready-to-use prompt context file

------------------------------------------------------------------------

## Location

    ScriptUtils/Core/PromptContextCollector/PromptContextCollector.py

------------------------------------------------------------------------

## Features

-   Recursive directory scanning
-   Glob-based include pattern filtering
-   Glob-based ignore pattern filtering
-   Explicit file inclusion support
-   Template variable substitution
-   Structured "Source Blob" output format
-   AI-ready prompt generation

------------------------------------------------------------------------

## Initialization

``` python
PromptContextCollector(
    directories,
    files,
    includes,
    ignores,
    template_path,
    template_vars,
    output_path
)
```

### Parameters

  -----------------------------------------------------------------------
  Parameter                   Type          Description
  --------------------------- ------------- -----------------------------
  `directories`               list\[str\]   Directories (relative to
                                            project root) to scan

  `files`                     list\[str\]   Specific files to always
                                            include

  `includes`                  list\[str\]   Glob patterns for allowed
                                            filenames

  `ignores`                   list\[str\]   Glob patterns for excluded
                                            paths

  `template_path`             str           Path to prompt template file

  `template_vars`             dict          Variables to replace in
                                            template

  `output_path`               str           Output file path (relative to
                                            project root)
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## Example Usage

``` python
from Core.PromptContextCollector.PromptContextCollector import PromptContextCollector

collector = PromptContextCollector(
    directories=["ScriptUtils/Core"],
    files=["ScriptUtils/readme.md"],
    includes=["*.py", "*.json", "*.md"],
    ignores=["__pycache__/*", "*.log"],
    template_path="Templates/prompt_template.txt",
    template_vars={
        "PROJECT_NAME": "UserProject",
        "AUTHOR": "DevTeam"
    },
    output_path="PromptAnalyzeScriptUtils.txt"
)

collector.run()
```

------------------------------------------------------------------------

## Output Structure

The generated output file contains:

1.  `// --- Source Blob ---`
2.  Full content of each collected file (wrapped with Start/End markers)
3.  `// --- Prompt ---`
4.  The processed template with substituted variables

This format is optimized for AI prompt analysis and structured context
injection.

------------------------------------------------------------------------

## How It Works

1.  Resolves project root automatically.
2.  Scans specified directories recursively.
3.  Applies include + ignore filters.
4.  Adds explicitly specified files.
5.  Writes file contents into a structured output file.
6.  Substitutes template variables.
7.  Appends the generated prompt section.

------------------------------------------------------------------------

## Filtering Rules

-   `files` are always included (if they exist).
-   `includes` apply to filenames.
-   `ignores` apply to relative paths.
-   Uses standard glob syntax (`fnmatch`).

------------------------------------------------------------------------

## Use Cases

-   AI code review prompts
-   Context packaging for LLM tools
-   Automated documentation bundles
-   Codebase snapshot generation
-   Structured debugging exports

------------------------------------------------------------------------

## Notes

-   All paths are interpreted relative to project root.
-   Template file must exist or execution will raise error.
-   Output file is overwritten on each run.

------------------------------------------------------------------------

Generated on: 2026-02-18 22:27:39
