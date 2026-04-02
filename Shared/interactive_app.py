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

    def _load_or_create_presets(self):
        path = self._get_preset_file()
        data = None

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = None

        if not isinstance(data, dict):
            data = {}

        self.ui_state = data.get("ui", {
            "help_open": True,
            "params_open": True,
            "presets_open": True
        })

        raw_presets = data.get("presets", [])

        self.presets = [
            p for p in raw_presets
            if isinstance(p, dict) and "name" in p and "values" in p
        ]

        if not any(p["name"] == "Default" for p in self.presets):
            self.presets.insert(0, {
                "name": "Default",
                "values": self._get_default_snapshot()
            })

        self.selected_preset = "Default"

        self._save_presets()

    def _save_presets(self):
        path = self._get_preset_file()
        data = {"ui": self.ui_state, "presets": self.presets}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _ui_log_sink(self, msg):
        self.log_lines.append(msg)
        if dpg.does_item_exist("log_text"):
            dpg.set_value("log_text", "\n".join(self.log_lines))

    def _apply_preset(self, preset):
        if not preset or "values" not in preset:
            return

        values = preset["values"]

        for g in self.context.groups:
            for p in g.params:
                if p.name in values:
                    p.value = values[p.name]

        self.selected_preset = preset["name"]
        self.logger.log(f"[PRESET] Applied: {preset['name']}")

        self._refresh_param_widgets()

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

    def _render_parameters(self):
        for group in self.context.groups:
            dpg.add_text(f"[{group.name}]", color=(150, 150, 150))

            for param in group.params:
                tag = param.name
                value = param.value

                if param.hints:
                    if isinstance(param.hints, dict):
                        items = list(param.hints.keys())
                        current_label = next(
                            (k for k, v in param.hints.items() if v == value),
                            items[0]
                        )
                        dpg.add_combo(items=items, default_value=current_label, tag=tag, label=param.name)
                    else:
                        dpg.add_combo(items=[str(x) for x in param.hints], default_value=str(value), tag=tag, label=param.name)

                elif param.type == bool:
                    dpg.add_checkbox(label=param.name, default_value=bool(value), tag=tag)

                elif param.type == int:
                    dpg.add_input_int(label=param.name, default_value=int(value), tag=tag)

                else:
                    dpg.add_input_text(label=param.name, default_value=str(value), tag=tag)

    def _render_presets_list(self):
        if dpg.does_item_exist("presets_container"):
            dpg.delete_item("presets_container", children_only=True)

        with dpg.group(tag="presets_container"):
            for preset in self.presets:
                name = preset["name"]
                is_selected = (name == self.selected_preset)
                label = f"> {name}" if is_selected else name
                color = (255, 255, 0) if is_selected else (200, 200, 200)

                btn = dpg.add_button(
                    label=label,
                    width=-1,
                    callback=lambda s, a, u=preset: self._apply_preset(u)
                )

                dpg.bind_item_theme(btn, self._create_text_theme(color))

            with dpg.group(horizontal=True):
                dpg.add_button(label="Save")
                dpg.add_button(label="Clone")
                dpg.add_button(label="Delete")

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
            with dpg.collapsing_header(label="", default_open=self.ui_state.get("help_open", True)):
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
            with dpg.collapsing_header(label="", default_open=self.ui_state.get("params_open", True)):
                self._render_parameters()

            dpg.add_text("### PRESETS", color=(255, 255, 0))
            with dpg.collapsing_header(label="", default_open=self.ui_state.get("presets_open", True)):
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
                    if p.type == bool:
                        p.value = bool(raw)
                    elif p.type == int:
                        p.value = int(raw)
                    else:
                        p.value = str(raw)
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
        dpg.destroy_context()

        return self.context if self.result else None