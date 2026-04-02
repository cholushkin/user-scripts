# Shared/im_ui.py

from dearpygui import dearpygui as dpg
import os


class ImUI:
    def __init__(self, context, logger, presets, binder, title="Interactive"):
        self.context = context
        self.logger = logger
        self.presets = presets
        self.binder = binder

        self.title = title
        self.result = None
        self.log_lines = []

    # -------------------------
    # BUILD
    # -------------------------
    def build(self):
        dpg.create_context()

        self._build_main_window()
        self._build_log_window()

        self.logger.attach_ui(self._log_sink)

        self.presets.apply(self.presets.selected)
        self.binder.push_to_ui()

    # -------------------------
    # MAIN WINDOW
    # -------------------------
    def _build_main_window(self):
        with dpg.window(label=self.title, width=650, height=900):

            # HELP
            dpg.add_text("### HELP", color=(255, 255, 0))
            with dpg.collapsing_header(tag="help_header",
                                       default_open=self.presets.ui_state.get("help_open", True)):
                dpg.add_button(label="How it works", callback=self._show_help_popup)

                for group in self.context.groups:
                    dpg.add_text(f"[{group.name}]", color=(150, 150, 150))

                    for p in group.params:
                        with dpg.group(horizontal=True):
                            dpg.add_text(f"-- {p.name} =")
                            dpg.add_text(str(p.default), color=(255, 255, 0))

                        if p.description:
                            dpg.add_text(p.description, color=(120, 120, 120))

            # PARAMETERS
            dpg.add_text("### PARAMETERS", color=(255, 255, 0))
            with dpg.collapsing_header(tag="params_header",
                                       default_open=self.presets.ui_state.get("params_open", True)):
                self.binder.render()

            # PRESETS
            dpg.add_text("### PRESETS", color=(255, 255, 0))
            with dpg.collapsing_header(tag="presets_header",
                                       default_open=self.presets.ui_state.get("presets_open", True)):
                self._render_presets()

            dpg.add_separator()

            # ACTIONS
            with dpg.group(horizontal=True):
                run_btn = dpg.add_button(label="Run", width=120, height=40, callback=self._on_run)
                cancel_btn = dpg.add_button(label="Cancel", width=120, height=40, callback=self._on_cancel)

                dpg.bind_item_theme(run_btn, self._button_theme((0, 120, 0)))
                dpg.bind_item_theme(cancel_btn, self._button_theme((200, 120, 0)))

    # -------------------------
    # LOG WINDOW
    # -------------------------
    def _build_log_window(self):
        with dpg.window(label="Log", pos=(700, 10), width=600, height=740):
            dpg.add_button(label="Clear", callback=self._clear_log)
            dpg.add_separator()
            dpg.add_text("", tag="log_text", wrap=580)

    # -------------------------
    # LOGGING
    # -------------------------
    def _log_sink(self, line):
        self.log_lines.append(line)
        if dpg.does_item_exist("log_text"):
            dpg.set_value("log_text", "\n".join(self.log_lines))

    def _clear_log(self):
        self.log_lines.clear()
        if dpg.does_item_exist("log_text"):
            dpg.set_value("log_text", "")

    # -------------------------
    # PRESETS UI
    # -------------------------
    def _render_presets(self):
        with dpg.group(tag="presets_container"):
            self._rebuild_presets()

    def _make_cb(self, name):
        return lambda: self._on_preset_click(name)

    def _rebuild_presets(self):
        dpg.delete_item("presets_container", children_only=True)

        with dpg.group(parent="presets_container"):
            for p in self.presets.list():
                name = p["name"]
                selected = (name == self.presets.selected)

                btn = dpg.add_button(
                    label=f"> {name}" if selected else name,
                    width=-1,
                    callback=self._make_cb(name)
                )

                dpg.bind_item_theme(btn, self._text_theme(
                    (255, 255, 0) if selected else (200, 200, 200)
                ))

            with dpg.group(horizontal=True):
                dpg.add_button(label="Save", callback=self._open_save_popup)
                dpg.add_button(label="Delete", callback=self._open_delete_popup)

    # -------------------------
    # PRESET ACTIONS
    # -------------------------
    def _on_preset_click(self, name):
        self.presets.apply(name)
        self.binder.push_to_ui()
        self._rebuild_presets()

    # ---------- SAVE ----------
    def _open_save_popup(self):
        with dpg.window(label="Save Preset", modal=True, width=400, height=200, tag="save_popup"):
            dpg.add_text("SAVE is not safe operation.\nType preset name to override.")
            dpg.add_input_text(tag="save_input", default_value=self.presets.selected or "")
            dpg.add_button(label="Confirm", callback=self._confirm_save)
            dpg.add_button(label="Cancel", callback=lambda: dpg.delete_item("save_popup"))

    def _confirm_save(self):
        self.binder.collect()

        name = dpg.get_value("save_input").strip()
        if not name:
            self.logger.warn("[PRESET] Invalid name")
            return

        self.presets.save(name)

        dpg.delete_item("save_popup")
        self._rebuild_presets()

    # ---------- DELETE ----------
    def _open_delete_popup(self):
        with dpg.window(label="Delete Preset", modal=True, width=400, height=200, tag="delete_popup"):
            dpg.add_text("DELETE is not safe operation.\nType preset name to confirm.")
            dpg.add_input_text(tag="delete_input")
            dpg.add_button(label="Confirm", callback=self._confirm_delete)
            dpg.add_button(label="Cancel", callback=lambda: dpg.delete_item("delete_popup"))

    def _confirm_delete(self):
        name = dpg.get_value("delete_input")

        self.presets.delete(name)

        dpg.delete_item("delete_popup")
        self._rebuild_presets()

    # -------------------------
    # ACTIONS
    # -------------------------
    def _on_run(self):
        self.binder.collect()
        self.result = True
        dpg.stop_dearpygui()

    def _on_cancel(self):
        self.result = None
        dpg.stop_dearpygui()

    # -------------------------
    # THEMES
    # -------------------------
    def _button_theme(self, color):
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, color)
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonHovered,
                    [min(c + 40, 255) for c in color]
                )
        return theme

    def _text_theme(self, color):
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Text, color)
        return theme

    # -------------------------
    # HELP
    # -------------------------
    def _load_help_text(self):
        path = os.path.join(os.path.dirname(__file__), "how_it_works.txt")
        try:
            return open(path, encoding="utf-8").read()
        except:
            return "Help file not found"

    def _show_help_popup(self):
        with dpg.window(label="Help", modal=True, width=500, height=400):
            dpg.add_text(self._load_help_text(), wrap=450)

    # -------------------------
    # RUN LOOP
    # -------------------------
    def run(self):
        self.build()

        dpg.create_viewport(title=self.title, width=1400, height=1000)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()

        self._save_state()
        dpg.destroy_context()

        return self.context if self.result else None

    # -------------------------
    # UI STATE
    # -------------------------
    def _save_state(self):
        for k, tag in [
            ("help_open", "help_header"),
            ("params_open", "params_header"),
            ("presets_open", "presets_header")
        ]:
            try:
                self.presets.ui_state[k] = dpg.get_value(tag)
            except:
                pass

        self.presets._save()