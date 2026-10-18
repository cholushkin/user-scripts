# GitUtils

Git submodule management plus a human-readable repository status report (submodule
state, Git LFS, hooks, and a curated set of repo-level options). Combines and extends
the old `ScriptUtils/Core/GitSubmoduleManager`.

## Quick Start (CLI)

```
gitutils --action status
```

Or directly through the launcher:

```
epy "c:\Apps\user-scripts\Modules\GitUtils\GitUtilsScript.py" --action force_update
```

## Interactive Mode

Hold **Left Ctrl** while launching `gitutils` (or pass `--interactive`) to open the Dear
PyGui UI.

## Parameters

### Action

| Param | Default | Description |
| --- | --- | --- |
| `action` | `status` | One of `status`, `force_update`, `add_submodule`, `remove_submodule`. |

### Submodules

| Param | Default | Description |
| --- | --- | --- |
| `repo_url` | `""` | Repository URL. Used by `add_submodule`. |
| `submodule_path` | `""` | Path (relative to the repo root) of the submodule. Used by `add_submodule` and `remove_submodule`. |

### Shared (from `BaseScript`)

`log_level`, `log_file`, `interactive`.

## Repository resolution

`gitutils` walks up from `--cwd`/`--selected` (or the current working directory if
neither is set) looking for a `.git` directory, so it works whether you run it from a
terminal or trigger it from a file manager with a folder/file selected.

## Actions

### `status`

Prints, in human-readable form:

- **Submodules** — count, and for each one its path, current branch, and short commit
  SHA (or `(not initialized)` if it hasn't been checked out yet).
- **LFS** — whether `git-lfs` is installed on this machine, whether it's initialized for
  this repo (`git lfs install`), and how many patterns are tracked via `.gitattributes`.
- **Hooks connected** — the resolved hooks directory (respects `core.hooksPath`) and
  which of the standard hooks (`pre-commit`, `pre-push`, `commit-msg`, `post-checkout`,
  `post-merge`, `pre-rebase`) are actually wired up (present and not just the Git-provided
  `*.sample` stub).
- **Options** — a curated set of repo-level Git config keys relevant to day-to-day use
  (`core.autocrlf`, `core.ignorecase`, `submodule.recurse`, `pull.rebase`,
  `fetch.recurseSubmodules`, `push.recurseSubmodules`, `status.submodulesummary`), each
  with a plain-English description and its current enabled/disabled/value state.

### `force_update`

Git submodules pin an exact commit and do **not** auto-update — `git submodule update`
checks out the recorded commit, not the latest one. This action:

1. `git submodule sync --recursive`
2. `git submodule update --init --recursive`
3. For each submodule: fetch `origin`, detect its default branch, fix a detached HEAD
   (checkout the branch, creating it from `origin/<branch>` if needed), then
   `git pull origin <branch>`.
4. `git add .` in the root repo to stage the updated submodule pointers.

Review and commit the staged pointer changes afterward (`git commit -m "Update submodules"`).

### `add_submodule` / `remove_submodule`

Standard `git submodule add`/`deinit`/`rm` wrapped with the usual cleanup (`.git/modules`
and the working-tree folder are removed on `remove_submodule`, even if the submodule was
only partially initialized).

## Notes

- For strict, reproducible version pinning (e.g. release branches), prefer manual
  submodule pinning over `force_update` — it is best suited for actively-developed
  internal libraries used as live dependencies.
