# PrintTree

Recursively lists (and optionally dumps the contents of) a directory tree. Handy for
building an LLM-friendly snapshot of a project — a file list plus the raw text of the
files that matter, wrapped in `<file path="...">` tags.

## Quick Start (CLI)

```
tree --path "D:/Project" --print_full_list --print_files_content
```

Or directly through the launcher:

```
epy "c:\Apps\user-scripts\Modules\PrintTree\print_tree.py" --path "D:/Project"
```

## Interactive Mode

Hold **Left Ctrl** while launching `tree` (or pass `--interactive`) to open the Dear
PyGui UI and tweak parameters/presets before running.

## Parameters

### Basic

| Param | Default | Description |
| --- | --- | --- |
| `path` | `.` | Starting location (file or directory). If it doesn't resolve, falls back to `--cwd`. |
| `print_full_list` | `True` | Print the full path of every discovered file. |
| `print_files_content` | `False` | Also print the isolated content of files matching `content_patterns`. |
| `log_name_from_dir` | `False` | Override the log filename to match the target directory name (e.g. `MyProject.log`). |

### Content

| Param | Default | Description |
| --- | --- | --- |
| `prefix_text_md` | `""` | Markdown file (relative to the active preset/config folder) whose raw content is printed first. See below. |
| `content_patterns` | `*.py;*.txt;*.md;*.cmd;*.bat;*.css;*.cs;*.asmref;*.asmdef` | Semicolon-separated patterns; matching files have their content printed. |
| `content_ignore_patterns` | `""` | Patterns excluded from content printing even if they match `content_patterns`. |
| `ignore_patterns` | `__pycache__;*.pyc;.git` | Files/folders skipped entirely (not listed, not read). |

### Shared (from `BaseScript`)

`log_level`, `log_file` (defaults to `Tree.log`), `interactive`.

## `prefix_text_md`

`prefix_text_md` points at a markdown file whose content is dumped verbatim before the
file list — useful for prepending a role/instructions block for an LLM. Two ready-made
prompt templates ship in this module for that purpose:

- **`analyze-code.md`** — an "Architecture Guardian" prompt for reviewing a module's
  structure, risk, and roadmap before making changes.
- **`generate-user-readme.md`** — the prompt template used to generate module
  `README.md` files like this one (Introduction / Features / Summary sections).

Set `prefix_text_md` to one of these filenames and it will be resolved relative to the
active preset's config directory (global: next to `print_tree.py`; local: the project's
`.uscript` folder).

## Output

1. (Optional) raw dump of `prefix_text_md`.
2. `### FILE LIST (N files discovered):` — one path per line.
3. (Optional) `### FILES CONTENT:` — each matching file wrapped as:
   ```
   <file path="...">
   ...file content...
   </file>
   ```

Output goes to stdout and, if `log_file` is set, to that log file in the current
working directory (or `<DirName>.log` when `log_name_from_dir` is enabled).
