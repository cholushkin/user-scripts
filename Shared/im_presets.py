# Shared/im_presets.py

import os
import sys
import json
from typing import Dict, List, Optional


class ImPresets:
    def __init__(self, context, logger, target_dir: Optional[str] = None, scope_name: str = "Global"):
        self.context = context
        self.logger = logger
        self.target_dir = target_dir
        self.scope_name = scope_name

        self.presets: List[Dict] = []
        self.ui_state: Dict = {}
        self.selected: Optional[str] = None

        self._load()

    def _get_file(self) -> str:
        script_path = os.path.abspath(sys.argv[0])
        script_name = os.path.splitext(os.path.basename(script_path))[0]
        
        # If a target directory (such as a project's .uscript folder) is provided, use it;
        # otherwise, fall back to the directory containing the script.
        base_dir = self.target_dir if self.target_dir else os.path.dirname(script_path)
        return os.path.join(base_dir, f"{script_name}.presets.json")

    def _defaults_snapshot(self) -> Dict:
        return {
            p.name: p.value
            for g in self.context.groups
            for p in g.params
        }

    def _current_snapshot(self) -> Dict:
        return {p.name: p.value for g in self.context.groups for p in g.params}

    def _load(self):
        path = self._get_file()
        data = None

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.logger.info(f"[{self.scope_name} PRESET] Loaded: {path}")
            except Exception as e:
                self.logger.warn(f"[{self.scope_name} PRESET] Failed to read, recreating: {e}")
        else:
            self.logger.info(f"[{self.scope_name} PRESET] No preset file found at: {path}")

        if not isinstance(data, dict):
            data = {}

        self.ui_state = data.get("ui", {
            "help_open": True,
            "params_open": True,
            "presets_open": True,
        })

        raw = data.get("presets", [])
        self.presets = [
            p for p in raw
            if isinstance(p, dict) and "name" in p and "values" in p
        ]

        # Only automatically create and enforce a "Default" preset for the Global scope.
        if self.scope_name == "Global" and not any(p["name"] == "Default" for p in self.presets):
            self.presets.insert(0, {
                "name": "Default",
                "values": self._defaults_snapshot()
            })
            self.logger.info(f"[{self.scope_name} PRESET] Default created")
            self._save()

        self.selected = self.presets[0]["name"] if self.presets else None

    def _save(self):
        path = self._get_file()
        data = {"ui": self.ui_state, "presets": self.presets}

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"[{self.scope_name} PRESET] Saved: {path}")
        except Exception as e:
            self.logger.error(f"[{self.scope_name} PRESET] Save failed: {e}")

    def apply(self, name: str):
        if not name:
            return

        preset = self.get(name)
        if not preset:
            self.logger.warn(f"[{self.scope_name} PRESET] Not found: {name}")
            return

        values = preset["values"].copy()
        for g in self.context.groups:
            for p in g.params:
                if p.name in values:
                    p.value = values[p.name]

        self.selected = name
        self.logger.info(f"[{self.scope_name} PRESET] Applied: {name}")

    def save(self, name: str):
        if not name:
            self.logger.warn(f"[{self.scope_name} PRESET] Invalid name")
            return

        snapshot = self._current_snapshot()

        for p in self.presets:
            if p["name"] == name:
                p["values"] = snapshot
                self.logger.info(f"[{self.scope_name} PRESET] Overwritten: {name}")
                break
        else:
            self.presets.append({"name": name, "values": snapshot})
            self.logger.info(f"[{self.scope_name} PRESET] Created: {name}")

        self.selected = name
        self._save()

    def delete(self, name: str):
        if self.scope_name == "Global" and name == "Default":
            self.logger.warn("[Global PRESET] Cannot delete Default")
            return

        self.presets = [p for p in self.presets if p["name"] != name]
        self.selected = self.presets[0]["name"] if self.presets else None
        self._save()

    def get(self, name: str) -> Optional[Dict]:
        for p in self.presets:
            if p["name"] == name:
                return p
        return None

    def list(self) -> List[Dict]:
        return self.presets