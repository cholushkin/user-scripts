from dearpygui import dearpygui as dpg
import os
import json
import sys
from interactive_logger import InteractiveLogger

HOST_WINDOW_WIDTH = 1400
HOST_WINDOW_HEIGHT = 1000
SCRIPT_WINDOW_WIDTH = 650
SCRIPT_WINDOW_HEIGHT = 900
LOG_WINDOW_WIDTH = 600
LOG_WINDOW_HEIGHT = 740
HELP_FILE = "how_it_works.txt"


class InteractiveApp:
    def __init__(self, context, title="Script"):
        self.context = context
        self.title = title
        self.result = None

        self.presets = []
        self.ui_state = {}
        self.selected_preset = None

        self.logger = InteractiveLogger()
        self.log_lines = []

        self._load_or_create_presets()

    def _get_preset_file(self):
        script_path = os.path.abspath(sys.argv[0])
        script_dir = os.path.dirname(script_path)
        script_name = os.path.splitext(os.path.basename(script_path))[0]
        return os.path.join(script_dir, f"{script_name}.presets.json")

    def _get_default_snapshot(self):
        return {p.name: p.default for g in self.context.groups for p in g.params}

    def _get_current_snapshot(self):
        return {p.name: p.value for g in self.context.groups for p in g.params}

    def _load_or_create_presets(self):
        path = self._get_preset_file()
        data = None

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.logger.log(f"[PRESET] Loaded: {path}")
            except Exception as e:
                self.logger.log(f"[PRESET] Failed to read, recreating: {e}")
                data = None
        else:
            self.logger.log(f"[PRESET] Creating new file: {path}")

        if not isinstance(data, dict):
            data = {}

        self.ui_state = data.get("ui", {
            "help_open": True,
            "params_open": True,
            "presets_open": True
        })

        raw = data.get("presets", [])
        self.presets = [
            p for p in raw
            if isinstance(p, dict) and "name" in p and "values" in p
        ]

        if not any(p["name"] == "Default" for p in self.presets):
            self.presets.insert(0, {
                "name": "Default",
                "values": self._get_default_snapshot()
            })
            self.logger.log("[PRESET] Default created")

        self.selected_preset = "Default"
        self._save_presets()

    def _save_presets(self):
        path = self._get_preset_file()
        data = {"ui": self.ui_state, "presets": self.presets}

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self.logger.log(f"[PRESET] Saved: {path}")
        except Exception as e:
            self.logger.log(f"[PRESET] Save failed: {e}")

    def _sync_ui_state(self):
        for key, tag in [
            ("help_open", "help_header"),
            ("params_open", "params_header"),
            ("presets_open", "presets_header"),
        ]:
            try:
                self.ui_state[key] = dpg.get_value(tag)
            except Exception:
                pass

    def _ui_log_sink(self, msg):
        self.log_lines.append(msg)
        if dpg.does_item_exist("log_text"):
            dpg.set_value("log_text", "\n".join(self.log_lines))

    def _clear_log(self):
        self.log_lines.clear()
        if dpg.does_item_exist("log_text"):
            dpg.set_value("log_text", "")

    def _on_preset_click(self, sender, app_data, user_data):
        self._apply_preset(user_data)

    def _apply_preset(self, preset):
        if not preset or "values" not in preset:
            return

        for g in self.context.groups:
            for p in g.params:
                if p.name in preset["values"]:
                    p.value = preset["values"][p.name]

        self.selected_preset = preset["name"]
        self.logger.log(f"[PRESET] Applied: {preset['name']}")

        self._refresh_param_widgets()
        self._rebuild_presets_ui()

    def _refresh_param_widgets(self):
        for g in self.context.groups:
            for p in g.params:
                if dpg.does_item_exist(p.name):
                    try:
                        dpg.set_value(p.name, p.value)
                    except Exception:
                        pass

    def _load_help_text(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, HELP_FILE)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _open_save_popup(self):
        with dpg.window(label="Save Preset", modal=True, width=400, height=200, tag="save_popup"):
            dpg.add_text("SAVE is not safe operation.\nType preset name to override.")
            dpg.add_input_text(tag="save_input", default_value=self.selected_preset or "")
            dpg.add_button(label="Confirm", callback=self._confirm_save)
            dpg.add_button(label="Cancel", callback=lambda: dpg.delete_item("save_popup"))

    def _confirm_save(self):
        name = dpg.get_value("save_input")

        for p in self.presets:
            if p["name"] == name:
                p["values"] = self._get_current_snapshot()
                self.logger.log(f"[PRESET] Overwritten: {name}")
                break
        else:
            self.presets.append({
                "name": name,
                "values": self._get_current_snapshot()
            })
            self.logger.log(f"[PRESET] Created: {name}")

        self.selected_preset = name
        self._save_presets()

        dpg.delete_item("save_popup")
        self._rebuild_presets_ui()

    def _open_delete_popup(self):
        with dpg.window(label="Delete Preset", modal=True, width=400, height=200, tag="delete_popup"):
            dpg.add_text("DELETE is not safe operation.\nType preset name to confirm.")
            dpg.add_input_text(tag="delete_input")
            dpg.add_button(label="Confirm", callback=self._confirm_delete)
            dpg.add_button(label="Cancel", callback=lambda: dpg.delete_item("delete_popup"))

    def _confirm_delete(self):
        name = dpg.get_value("delete_input")

        if name == "Default":
            self.logger.log("[PRESET] Cannot delete Default")
            return

        self.presets = [p for p in self.presets if p["name"] != name]
        self.logger.log(f"[PRESET] Deleted: {name}")

        self.selected_preset = "Default"
        self._save_presets()

        dpg.delete_item("delete_popup")
        self._rebuild_presets_ui()

    def _rebuild_presets_ui(self):
        if not dpg.does_item_exist("presets_container"):
            return

        dpg.delete_item("presets_container", children_only=True)

        with dpg.group(parent="presets_container"):
            self._render_presets_content()

    def _render_parameters(self):
        for group in self.context.groups:
            dpg.add_text(f"[{group.name}]", color=(150, 150, 150))

            for p in group.params:
                tag = p.name
                val = p.value

                if p.hints:
                    if isinstance(p.hints, dict):
                        items = list(p.hints.keys())
                        current = next((k for k, v in p.hints.items() if v == val), items[0])
                        dpg.add_combo(items=items, default_value=current, tag=tag, label=p.name)
                    else:
                        dpg.add_combo(items=[str(x) for x in p.hints], default_value=str(val), tag=tag, label=p.name)
                elif p.type == bool:
                    dpg.add_checkbox(label=p.name, default_value=bool(val), tag=tag)
                elif p.type == int:
                    dpg.add_input_int(label=p.name, default_value=int(val), tag=tag)
                else:
                    dpg.add_input_text(label=p.name, default_value=str(val), tag=tag)

    def _render_presets_list(self):
        with dpg.group(tag="presets_container"):
            self._render_presets_content()

    def _render_presets_content(self):
        for preset in self.presets:
            name = preset["name"]
            selected = (name == self.selected_preset)
            label = f"> {name}" if selected else name
            color = (255, 255, 0) if selected else (200, 200, 200)

            btn = dpg.add_button(
                label=label,
                width=-1,
                callback=self._on_preset_click,
                user_data=preset
            )

            dpg.bind_item_theme(btn, self._create_text_theme(color))

        with dpg.group(horizontal=True):
            dpg.add_button(label="Save", callback=self._open_save_popup)
            dpg.add_button(label="Delete", callback=self._open_delete_popup)

    def _create_text_theme(self, color):
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Text, color)
        return theme

    def _create_main_button_theme(self, color):
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, color)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [min(c + 30, 255) for c in color])
        return theme

    def _build(self):
        dpg.create_context()

        with dpg.window(label=self.title, width=SCRIPT_WINDOW_WIDTH, height=SCRIPT_WINDOW_HEIGHT):

            dpg.add_text("### HELP", color=(255, 255, 0))
            with dpg.collapsing_header(tag="help_header", default_open=self.ui_state.get("help_open", True)):
                dpg.add_button(label="How it works", callback=self._show_help_popup)

                for group in self.context.groups:
                    dpg.add_text(f"[{group.name}]", color=(150, 150, 150))
                    for p in group.params:
                        with dpg.group(horizontal=True):
                            dpg.add_text(f"-- {p.name} =")
                            dpg.add_text(str(p.default), color=(255, 255, 0))
                        if p.description:
                            dpg.add_text(p.description, color=(120, 120, 120))

            dpg.add_text("### PARAMETERS", color=(255, 255, 0))
            with dpg.collapsing_header(tag="params_header", default_open=self.ui_state.get("params_open", True)):
                self._render_parameters()

            dpg.add_text("### PRESETS", color=(255, 255, 0))
            with dpg.collapsing_header(tag="presets_header", default_open=self.ui_state.get("presets_open", True)):
                self._render_presets_list()

            dpg.add_separator()

            def on_run():
                self._collect_values()
                dpg.stop_dearpygui()

            def on_cancel():
                self.result = None
                dpg.stop_dearpygui()

            with dpg.group(horizontal=True):
                run_btn = dpg.add_button(label="Run", width=120, height=40, callback=on_run)
                cancel_btn = dpg.add_button(label="Cancel", width=120, height=40, callback=on_cancel)

                dpg.bind_item_theme(run_btn, self._create_main_button_theme([0, 120, 0]))
                dpg.bind_item_theme(cancel_btn, self._create_main_button_theme([120, 0, 0]))

        with dpg.window(label="Log",
                        pos=(SCRIPT_WINDOW_WIDTH + 20, 10),
                        width=LOG_WINDOW_WIDTH,
                        height=LOG_WINDOW_HEIGHT):

            with dpg.group(horizontal=True):
                dpg.add_button(label="Clear", callback=self._clear_log)

            dpg.add_separator()
            dpg.add_text("", tag="log_text", wrap=LOG_WINDOW_WIDTH - 20)

        self.logger.attach_ui(self._ui_log_sink)

        default = next(p for p in self.presets if p["name"] == "Default")
        self._apply_preset(default)

    def _show_help_popup(self):
        with dpg.window(label="Interactive Mode Help", modal=True, width=500, height=400):
            dpg.add_text(self._load_help_text(), wrap=450)

    def _collect_values(self):
        for g in self.context.groups:
            for p in g.params:
                raw = dpg.get_value(p.name)
                if isinstance(p.hints, dict):
                    raw = p.hints.get(raw, raw)
                try:
                    p.value = p.type(raw)
                except Exception:
                    pass
        self.result = True

    def run(self):
        self._build()

        dpg.create_viewport(
            title=self.title,
            width=HOST_WINDOW_WIDTH,
            height=HOST_WINDOW_HEIGHT
        )

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()

        self._sync_ui_state()
        self._save_presets()

        dpg.destroy_context()
        return self.context if self.result else None