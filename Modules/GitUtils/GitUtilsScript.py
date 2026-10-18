import os
import sys
import shutil
import subprocess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Shared")))

from base_script import BaseScript
from context import ParamGroup
from param import Param


DEFAULTS = {
    "log_level": 20,
    "log_file": None,

    "action": "status",
    "repo_url": "",
    "submodule_path": "",
}

STANDARD_HOOKS = ["pre-commit", "pre-push", "commit-msg", "post-checkout", "post-merge", "pre-rebase"]

GIT_OPTION_DESCRIPTIONS = {
    "core.autocrlf": "Automatic CRLF/LF line-ending conversion",
    "core.ignorecase": "Case-insensitive file matching",
    "submodule.recurse": "Git commands (checkout/pull/etc.) recurse into submodules automatically",
    "pull.rebase": "'git pull' rebases instead of merging",
    "fetch.recurseSubmodules": "'git fetch' recurses into submodules automatically",
    "push.recurseSubmodules": "Pushing also pushes submodule commits automatically",
    "status.submodulesummary": "'git status' shows a submodule change summary",
}


class GitUtilsScript(BaseScript):

    def define_groups(self):
        return [
            ParamGroup("Action", [
                Param(
                    "action",
                    str,
                    DEFAULTS["action"],
                    hints=["status", "force_update", "add_submodule", "remove_submodule"],
                    description="status: report submodules/LFS/hooks/options. force_update: sync and update "
                                "all submodules to their latest remote commit. add_submodule/remove_submodule: "
                                "use the fields in the Submodules section below."
                ),
            ]),
            ParamGroup("Submodules", [
                Param(
                    "repo_url",
                    str,
                    DEFAULTS["repo_url"],
                    label="Repository URL",
                    description="Used by action=add_submodule"
                ),
                Param(
                    "submodule_path",
                    str,
                    DEFAULTS["submodule_path"],
                    label="Submodule path",
                    description="Path (relative to the repo root) of the submodule. Used by add_submodule and remove_submodule"
                ),
            ]),
        ]

    def get_defaults(self):
        return DEFAULTS

    def preview(self, ctx):
        return f"GitUtils: {ctx['action']}"

    # -------------------------
    # GIT HELPERS
    # -------------------------
    def _run_git(self, args, cwd=None):
        result = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
        return result.stdout.strip()

    def _find_git_root(self, start):
        start = os.path.abspath(str(start))
        if os.path.isfile(start):
            start = os.path.dirname(start)

        curr = start
        while not os.path.isdir(os.path.join(curr, ".git")):
            parent = os.path.dirname(curr)
            if parent == curr:
                raise RuntimeError(f"Not inside a Git repository: {start}")
            curr = parent

        return curr

    def _get_submodules(self, root):
        try:
            output = self._run_git(["config", "--file", ".gitmodules", "--get-regexp", "path"], cwd=root)
        except RuntimeError:
            return []

        submodules = []
        for line in output.splitlines():
            parts = line.strip().split(" ")
            if len(parts) == 2:
                submodules.append(parts[1])
        return submodules

    def _get_default_branch(self, submodule_full_path):
        try:
            ref = self._run_git(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], cwd=submodule_full_path)
            return ref.replace("origin/", "")
        except RuntimeError:
            return "master"

    def _checkout_branch(self, path, branch):
        try:
            self._run_git(["checkout", branch], cwd=path)
        except RuntimeError:
            self._run_git(["checkout", "-b", branch, f"origin/{branch}"], cwd=path)

    # -------------------------
    # ACTIONS
    # -------------------------
    def _update_submodule_to_latest(self, root, sub_rel_path):
        full_path = os.path.join(root, sub_rel_path)
        self.log_info(f"Updating: {sub_rel_path}")

        try:
            self._run_git(["fetch", "origin"], cwd=full_path)
            branch = self._get_default_branch(full_path)
            self.log_debug(f"  branch: {branch}")
            self._checkout_branch(full_path, branch)
            self._run_git(["pull", "origin", branch], cwd=full_path)
        except Exception as e:
            self.log_error(f"Failed updating {sub_rel_path}: {e}")

    def _force_update_all_submodules(self, root):
        try:
            self.log_info("Syncing submodules")
            self._run_git(["submodule", "sync", "--recursive"], cwd=root)

            self.log_info("Initializing submodules")
            self._run_git(["submodule", "update", "--init", "--recursive"], cwd=root)
        except Exception as e:
            self.log_error(f"Force update failed: {e}")
            return

        submodules = self._get_submodules(root)
        if not submodules:
            self.log_info("No submodules found.")
            return

        for sub in submodules:
            self._update_submodule_to_latest(root, sub)

        try:
            self.log_info("Staging updated submodule pointers")
            self._run_git(["add", "."], cwd=root)
        except Exception as e:
            self.log_error(f"Failed to stage submodule pointers: {e}")
            return

        self.log_info("All submodules updated and staged.")

    def _add_submodule(self, root, repo_url, submodule_path):
        submodule_path = os.path.normpath(submodule_path)
        try:
            self._run_git(["submodule", "add", repo_url, submodule_path], cwd=root)
            self.log_info(f"Submodule added: {submodule_path}")

            self._run_git(["submodule", "update", "--init", submodule_path], cwd=root)
            self.log_info(f"Submodule updated: {submodule_path}")
        except Exception as e:
            self.log_error(str(e))

    def _remove_submodule(self, root, submodule_path):
        submodule_path = os.path.normpath(submodule_path)

        try:
            self._run_git(["submodule", "deinit", "-f", submodule_path], cwd=root)
        except RuntimeError:
            self.log_debug(f"Submodule not initialized or already removed: {submodule_path}")

        try:
            self._run_git(["rm", "-f", submodule_path], cwd=root)
        except RuntimeError:
            self.log_debug(f"Submodule already removed from git index: {submodule_path}")

        modules_path = os.path.join(root, ".git", "modules", submodule_path)
        if os.path.exists(modules_path):
            shutil.rmtree(modules_path)

        full_path = os.path.join(root, submodule_path)
        if os.path.exists(full_path):
            shutil.rmtree(full_path)

        self.log_info(f"Submodule removed: {submodule_path}")

    # -------------------------
    # STATUS REPORT
    # -------------------------
    def _print_status(self, root):
        self.log_info(f"Repository root: {root}")

        submodules = self._get_submodules(root)
        self.log_info(f"Submodules: {len(submodules)}")
        for sub in submodules:
            full_path = os.path.join(root, sub)
            if not os.path.exists(os.path.join(full_path, ".git")):
                self.log_info(f"  - {sub}  (not initialized)")
                continue

            try:
                branch = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=full_path)
            except RuntimeError:
                branch = "?"
            try:
                commit = self._run_git(["rev-parse", "--short", "HEAD"], cwd=full_path)
            except RuntimeError:
                commit = "?"

            self.log_info(f"  - {sub}  [{branch} @ {commit}]")

        self.log_info("")
        self._print_lfs_status(root)
        self.log_info("")
        self._print_hooks_status(root)
        self.log_info("")
        self._print_options(root)

    def _print_lfs_status(self, root):
        if shutil.which("git-lfs") is None:
            self.log_info("LFS: git-lfs is not installed on this machine")
            return

        try:
            filter_value = self._run_git(["config", "--get", "filter.lfs.process"], cwd=root)
        except RuntimeError:
            filter_value = None

        if not filter_value:
            self.log_info("LFS: git-lfs installed, but not initialized in this repo (run 'git lfs install')")
            return

        tracked_patterns = 0
        gitattributes_path = os.path.join(root, ".gitattributes")
        if os.path.isfile(gitattributes_path):
            with open(gitattributes_path, "r", encoding="utf-8", errors="ignore") as f:
                tracked_patterns = sum(1 for line in f if "filter=lfs" in line)

        self.log_info(f"LFS: installed & configured ({tracked_patterns} pattern(s) tracked in .gitattributes)")

    def _print_hooks_status(self, root):
        try:
            hooks_dir = self._run_git(["config", "core.hooksPath"], cwd=root)
        except RuntimeError:
            hooks_dir = None

        if hooks_dir:
            hooks_dir = hooks_dir if os.path.isabs(hooks_dir) else os.path.join(root, hooks_dir)
        else:
            hooks_dir = os.path.join(root, ".git", "hooks")

        self.log_info(f"Hooks directory: {hooks_dir}")

        connected = [hook for hook in STANDARD_HOOKS if os.path.isfile(os.path.join(hooks_dir, hook))]
        self.log_info(f"Hooks connected: {', '.join(connected) if connected else 'none'}")

    def _print_options(self, root):
        self.log_info("Options:")
        for key, description in GIT_OPTION_DESCRIPTIONS.items():
            try:
                value = self._run_git(["config", "--get", key], cwd=root)
            except RuntimeError:
                value = None

            if value is None:
                state = "not set (default)"
            elif value.lower() in ("true", "1", "yes"):
                state = "enabled"
            elif value.lower() in ("false", "0", "no"):
                state = "disabled"
            else:
                state = value

            self.log_info(f"  - {description}: {state}  [{key}]")

    # -------------------------
    # ENTRY
    # -------------------------
    def run(self, ctx):
        extra = getattr(self.context, "extra", {})
        start = extra.get("cwd") or extra.get("selected") or os.getcwd()

        try:
            root = self._find_git_root(start)
        except RuntimeError as e:
            self.log_error(str(e))
            return

        action = ctx["action"]

        if action == "status":
            self._print_status(root)

        elif action == "force_update":
            self._force_update_all_submodules(root)

        elif action == "add_submodule":
            repo_url = (ctx.get("repo_url") or "").strip()
            submodule_path = (ctx.get("submodule_path") or "").strip()
            if not repo_url or not submodule_path:
                self.log_error("repo_url and submodule_path are both required for add_submodule")
                return
            self._add_submodule(root, repo_url, submodule_path)

        elif action == "remove_submodule":
            submodule_path = (ctx.get("submodule_path") or "").strip()
            if not submodule_path:
                self.log_error("submodule_path is required for remove_submodule")
                return
            self._remove_submodule(root, submodule_path)

        else:
            self.log_error(f"Unknown action: {action}")


if __name__ == "__main__":
    GitUtilsScript().execute()
