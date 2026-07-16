# Shared/im_ui.py

import os
from typing import Optional
from dearpygui import dearpygui as dpg


class ImUI:
    def __init__(
        self,
        context,
        logger,
        presets,
        binder,
        project_presets: Optional[object] = None,
        project_name: Optional[str] = None,
        title: str = "Interactive",
    ):
        self.context = context
        self.logger = logger
        self.presets = presets  # Primary (Global) presets manager
        self.project_presets = project_presets  # Optional Project-domain presets manager
        self.project_name = project_name
        self.binder = binder

        self.title = title
        self.result = None
        self.log_lines = []

    # -------------------------
    # BUILD & INIT
    # -------------------------
    def build(self):
        dpg.create_context()

        self._build_main_window()
        self._build_log_window()

        self.logger.attach_ui(self._log_sink)

        # Apply initial preset and push synced values to UI
        if self.presets.selected:
            self.presets.apply(self.presets.selected)
        self.binder.push_to_ui()

    # -------------------------
    # MAIN WINDOW
    # -------------------------
    def _build_main_window(self):
        with dpg.window(label=self.title, width=650, height=900):

            # --- HELP SECTION ---
            dpg.add_text("### HELP", color=(255, 255, 0))
            with dpg.collapsing_header(
                tag="help_header",
                default_open=self.presets.ui_state.get("help_open", True),
            ):
                dpg.add_button(label="How it works", callback=self._show_help_popup)

                for group in self.context.groups:
                    dpg.add_text(f"[{group.name}]", color=(150, 150, 150))
                    for p in group.params:
                        with dpg.group(horizontal=True):
                            dpg.add_text(f"-- {p.name} =")
                            dpg.add_text(str(p.default), color=(255, 255, 0))
                        if p.description:
                            dpg.add_text(p.description, color=(120, 120, 120))

            # --- PARAMETERS SECTION ---
            dpg.add_text("### PARAMETERS", color=(255, 255, 0))
            with dpg.collapsing_header(
                tag="params_header",
                default_open=self.presets.ui_state.get("params_open", True),
            ):
                self.binder.render()

            # --- GLOBAL PRESETS ---
            dpg.add_text("### PRESETS", color=(255, 255, 0))
            with dpg.collapsing_header(
                tag="presets_header",
                default_open=self.presets.ui_state.get("presets_open", True),
            ):
                self._render_presets(self.presets, prefix="global")

            # --- PROJECT PRESETS ---
            if self.project_presets and self.project_name:
                dpg.add_text(f"### PRESETS [{self.project_name}]", color=(0, 255, 200))
                with dpg.collapsing_header(
                    tag="project_presets_header",
                    default_open=self.project_presets.ui_state.get("presets_open", True),
                ):
                    self._render_presets(self.project_presets, prefix="project")

            dpg.add_separator()

            # --- ACTION BUTTONS ---
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

    def _log_sink(self, line: str):
        self.log_lines.append(line)
        if dpg.does_item_exist("log_text"):
            dpg.set_value("log_text", "\n".join(self.log_lines))

    def _clear_log(self):
        self.log_lines.clear()
        if dpg.does_item_exist("log_text"):
            dpg.set_value("log_text", "")

    # -------------------------
    # PRESETS UI (Namespaced)
    # -------------------------
    def _render_presets(self, presets_mgr, prefix: str):
        with dpg.group(tag=f"presets_container_{prefix}"):
            self._rebuild_presets(presets_mgr, prefix)

    def _make_preset_cb(self, presets_mgr, prefix: str, name: str):
        return lambda: self._on_preset_click(presets_mgr, prefix, name)

    def _rebuild_presets(self, presets_mgr, prefix: str):
        container = f"presets_container_{prefix}"
        dpg.delete_item(container, children_only=True)

        with dpg.group(parent=container):
            for p in presets_mgr.list():
                name = p["name"]
                selected = (name == presets_mgr.selected)

                btn = dpg.add_button(
                    label=f"> {name}" if selected else name,
                    width=-1,
                    callback=self._make_preset_cb(presets_mgr, prefix, name),
                )

                dpg.bind_item_theme(
                    btn,
                    self._text_theme((255, 255, 0) if selected else (200, 200, 200)),
                )

            with dpg.group(horizontal=True):
                dpg.add_button(label="Save", callback=lambda: self._open_save_popup(presets_mgr, prefix))
                dpg.add_button(label="Delete", callback=lambda: self._open_delete_popup(presets_mgr, prefix))

    def _on_preset_click(self, presets_mgr, prefix: str, name: str):
        # Deselect opposite scope to maintain a single active highlight across panels
        other_mgr = self.project_presets if presets_mgr == self.presets else self.presets
        if other_mgr:
            other_mgr.selected = None
            other_prefix = "project" if prefix == "global" else "global"
            if dpg.does_item_exist(f"presets_container_{other_prefix}"):
                self._rebuild_presets(other_mgr, other_prefix)

        presets_mgr.apply(name)
        self.binder.push_to_ui()
        self._rebuild_presets(presets_mgr, prefix)

    # -------------------------
    # PRESET MODALS
    # -------------------------
    def _open_save_popup(self, presets_mgr, prefix: str):
        popup, input_tag = f"save_popup_{prefix}", f"save_input_{prefix}"
        if dpg.does_item_exist(popup):
            dpg.delete_item(popup)

        with dpg.window(label="Save Preset", modal=True, width=400, height=200, tag=popup):
            dpg.add_text("SAVE is not safe operation.\nType preset name to override.")
            dpg.add_input_text(tag=input_tag, default_value=presets_mgr.selected or "")
            dpg.add_button(label="Confirm", callback=lambda: self._confirm_save(presets_mgr, prefix, input_tag, popup))
            dpg.add_button(label="Cancel", callback=lambda: dpg.delete_item(popup))

    def _confirm_save(self, presets_mgr, prefix: str, input_tag: str, popup_tag: str):
        self.binder.collect()
        name = dpg.get_value(input_tag).strip()
        
        if not name:
            self.logger.warn("[PRESET] Invalid name")
            return

        presets_mgr.save(name)
        dpg.delete_item(popup_tag)
        self._rebuild_presets(presets_mgr, prefix)

    def _open_delete_popup(self, presets_mgr, prefix: str):
        popup, input_tag = f"delete_popup_{prefix}", f"delete_input_{prefix}"
        if dpg.does_item_exist(popup):
            dpg.delete_item(popup)

        with dpg.window(label="Delete Preset", modal=True, width=400, height=200, tag=popup):
            dpg.add_text("DELETE is not safe operation.\nType preset name to confirm.")
            dpg.add_input_text(tag=input_tag)
            dpg.add_button(label="Confirm", callback=lambda: self._confirm_delete(presets_mgr, prefix, input_tag, popup))
            dpg.add_button(label="Cancel", callback=lambda: dpg.delete_item(popup))

    def _confirm_delete(self, presets_mgr, prefix: str, input_tag: str, popup_tag: str):
        name = dpg.get_value(input_tag)
        presets_mgr.delete(name)
        dpg.delete_item(popup_tag)
        self._rebuild_presets(presets_mgr, prefix)

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
                    [min(c + 40, 255) for c in color],
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
    def _load_help_text(self) -> str:
        path = os.path.join(os.path.dirname(__file__), "how_it_works.txt")
        try:
            with open(path, encoding="utf-8") as f:
                return f.read()
        except Exception:
            return "Help file not found"

    def _show_help_popup(self):
        with dpg.window(label="Help", modal=True, width=500, height=400):
            dpg.add_text(self._load_help_text(), wrap=450)

    # -------------------------
    # RUN LOOP & STATE
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

    def _save_state(self):
        for k, tag in [
            ("help_open", "help_header"),
            ("params_open", "params_header"),
            ("presets_open", "presets_header"),
        ]:
            try:
                self.presets.ui_state[k] = dpg.get_value(tag)
            except Exception:
                pass

        self.presets._save()

        # Persist project-level header state if project domain is active
        if self.project_presets:
            try:
                self.project_presets.ui_state["presets_open"] = dpg.get_value("project_presets_header")
                self.project_presets._save()
            except Exception:
                pass