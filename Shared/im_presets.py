import os
import sys
import json
from typing import Dict, List, Optional


class ImPresets:
    def __init__(self, context, logger):
        self.context = context
        self.logger = logger

        self.presets: List[Dict] = []
        self.ui_state: Dict = {}
        self.selected: str = "Default"

        self._load()

    def _get_file(self) -> str:
        script_path = os.path.abspath(sys.argv[0])
        script_dir = os.path.dirname(script_path)
        script_name = os.path.splitext(os.path.basename(script_path))[0]
        return os.path.join(script_dir, f"{script_name}.presets.json")

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
                self.logger.info(f"[PRESET] Loaded: {path}")
            except Exception as e:
                self.logger.warn(f"[PRESET] Failed to read, recreating: {e}")
        else:
            self.logger.info(f"[PRESET] Creating new file: {path}")

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

        if not any(p["name"] == "Default" for p in self.presets):
            self.presets.insert(0, {
                "name": "Default",
                "values": self._defaults_snapshot()
            })
            self.logger.info("[PRESET] Default created")

        self.selected = self.presets[0]["name"] if self.presets else "Default"

        self._save()

    def _save(self):
        path = self._get_file()
        data = {"ui": self.ui_state, "presets": self.presets}

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"[PRESET] Saved: {path}")
        except Exception as e:
            self.logger.error(f"[PRESET] Save failed: {e}")

    def apply(self, name: str):
        if not name:
            self.logger.warn("[PRESET] Invalid preset name")
            return

        preset = self.get(name)
        if not preset:
            self.logger.warn(f"[PRESET] Not found: {name}")
            return

        values = preset["values"].copy()

        for g in self.context.groups:
            for p in g.params:
                if p.name in values:
                    p.value = values[p.name]

        self.selected = name
        self.logger.info(f"[PRESET] Applied: {name}")

    def save(self, name: str):
        if not name:
            self.logger.warn("[PRESET] Invalid name")
            return

        snapshot = self._current_snapshot()

        for p in self.presets:
            if p["name"] == name:
                p["values"] = snapshot
                self.logger.info(f"[PRESET] Overwritten: {name}")
                break
        else:
            self.presets.append({"name": name, "values": snapshot})
            self.logger.info(f"[PRESET] Created: {name}")

        self.selected = name
        self._save()

    def delete(self, name: str):
        if name == "Default":
            self.logger.warn("[PRESET] Cannot delete Default")
            return

        self.presets = [p for p in self.presets if p["name"] != name]

        self.selected = "Default"
        self._save()

    def get(self, name: str) -> Optional[Dict]:
        for p in self.presets:
            if p["name"] == name:
                return p
        return None

    def list(self) -> List[Dict]:
        return self.presets