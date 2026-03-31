from dearpygui import dearpygui as dpg
import os


# -------------------------
# CONFIG
# -------------------------
VIEWPORT_WIDTH = 720
VIEWPORT_HEIGHT = 800

WINDOW_WIDTH = 700
WINDOW_HEIGHT = 700

HELP_FILE = "how_it_works.txt"


class InteractiveApp:
    def __init__(self, context, title="Script"):
        self.context = context
        self.title = title
        self.result = None

    # -------------------------
    # LOAD HELP (NO FALLBACK)
    # -------------------------
    def _load_help_text(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, HELP_FILE)

        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    # -------------------------
    # PARAMETERS UI (defined early as requested)
    # -------------------------
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

                        dpg.add_combo(
                            items=items,
                            default_value=current_label,
                            tag=tag,
                            label=param.name
                        )
                    else:
                        dpg.add_combo(
                            items=[str(x) for x in param.hints],
                            default_value=str(value),
                            tag=tag,
                            label=param.name
                        )

                elif param.type == bool:
                    dpg.add_checkbox(
                        label=param.name,
                        default_value=bool(value),
                        tag=tag
                    )

                elif param.type == int:
                    dpg.add_input_int(
                        label=param.name,
                        default_value=int(value),
                        tag=tag
                    )

                else:
                    dpg.add_input_text(
                        label=param.name,
                        default_value=str(value),
                        tag=tag
                    )

    # -------------------------
    # BUILD UI
    # -------------------------
    def _build(self):
        dpg.create_context()

        with dpg.window(
            label=self.title,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT
        ):

            # -------------------------
            # HELP (FIRST — unchanged order)
            # -------------------------
            dpg.add_text("### HELP", color=(255, 255, 0))
            dpg.add_separator()

            dpg.add_button(label="How it works", callback=self._show_help_popup)

            for group in self.context.groups:
                dpg.add_text(f"[{group.name}]", color=(150, 150, 150))

                for p in group.params:
                    with dpg.group(horizontal=True):
                        dpg.add_text(f"-- {p.name} =")
                        dpg.add_text(str(p.default), color=(255, 255, 0))

                    if p.description:
                        dpg.add_text(p.description, color=(120, 120, 120))

            # -------------------------
            # PARAMETERS (SECOND — unchanged order)
            # -------------------------
            dpg.add_spacer(height=10)
            dpg.add_text("### PARAMETERS", color=(255, 255, 0))
            dpg.add_separator()

            self._render_parameters()

            # -------------------------
            # PRESETS
            # -------------------------
            dpg.add_spacer(height=10)
            dpg.add_text("### PRESETS", color=(255, 255, 0))
            dpg.add_separator()
            dpg.add_text("(empty)", color=(120, 120, 120))

            # -------------------------
            # BUTTONS
            # -------------------------
            def on_run():
                self._collect_values()
                dpg.stop_dearpygui()

            def on_cancel():
                self.result = None
                dpg.stop_dearpygui()

            dpg.add_spacer(height=10)

            with dpg.group(horizontal=True):
                dpg.add_button(label="Run", callback=on_run)
                dpg.add_button(label="Cancel", callback=on_cancel)

    # -------------------------
    # HELP POPUP
    # -------------------------
    def _show_help_popup(self):
        with dpg.window(
            label="Interactive Mode Help",
            modal=True,
            width=500,
            height=400
        ):
            dpg.add_text(self._load_help_text(), wrap=450)

    # -------------------------
    # COLLECT VALUES
    # -------------------------
    def _collect_values(self):
        for group in self.context.groups:
            for param in group.params:
                raw = dpg.get_value(param.name)

                if isinstance(param.hints, dict):
                    raw = param.hints.get(raw, raw)

                try:
                    if param.type == bool:
                        param.value = bool(raw)
                    elif param.type == int:
                        param.value = int(raw)
                    else:
                        param.value = str(raw)
                except Exception:
                    pass

        self.result = True

    # -------------------------
    # RUN
    # -------------------------
    def run(self):
        self._build()

        dpg.create_viewport(
            title=self.title,
            width=VIEWPORT_WIDTH,
            height=VIEWPORT_HEIGHT
        )

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()

        return self.context if self.result else None