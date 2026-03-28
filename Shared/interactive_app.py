from dearpygui import dearpygui as dpg


class InteractiveApp:
    def __init__(self, context, title="Script"):
        self.context = context
        self.title = title
        self.result = None

    # -------------------------
    # HELP TEXT
    # -------------------------
    def _get_general_help(self):
        return (
            "INTERACTIVE MODE\n\n"
            "- Default values come from the script\n"
            "- CLI arguments override defaults\n"
            "- Interactive mode lets you override values before execution\n\n"
            "NOTES:\n"
            "- Changes here do NOT modify script defaults\n"
            "- Defaults must be edited in the script\n"
        )

    # -------------------------
    # BUILD UI
    # -------------------------
    def _build(self):
        dpg.create_context()

        with dpg.window(label=self.title):

            # -------------------------
            # HELP
            # -------------------------
            dpg.add_text("### HELP", color=(255, 255, 0))
            dpg.add_separator()

            dpg.add_button(label="How it works", callback=self._show_help_popup)

            for group in self.context.groups:
                dpg.add_text(f"[{group.name}]", color=(150, 150, 150))

                for p in group.params:
                    # compact line
                    with dpg.group(horizontal=True):
                        dpg.add_text(f"-- {p.name} =")
                        dpg.add_text(str(p.default), color=(255, 255, 0))

                    if p.description:
                        dpg.add_text(p.description, color=(120, 120, 120))

            # -------------------------
            # PARAMETERS
            # -------------------------
            dpg.add_spacer(height=10)
            dpg.add_text("### PARAMETERS", color=(255, 255, 0))
            dpg.add_separator()

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

                dpg.add_separator()

            # -------------------------
            # PRESETS
            # -------------------------
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
            dpg.add_text(self._get_general_help(), wrap=450)

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

        dpg.create_viewport(title=self.title, width=700, height=700)

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()

        return self.context if self.result else None