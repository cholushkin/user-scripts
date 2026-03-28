from prompt_toolkit import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, VSplit
from prompt_toolkit.widgets import Label, TextArea, Button
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style


def build_help_text():
    return "\n".join([
        "Navigation:",
        "  Tab / Shift+Tab  → move between fields",
        "  Arrow keys       → move cursor inside field",
        "  Mouse click      → focus field or button",
        "  Enter            → activate button (when focused)",
        "  Esc              → exit",
    ])


class InteractiveApp:
    def __init__(self, context, title="Script"):
        self.context = context
        self.title = title
        self.inputs = []

    def _build(self):
        rows = []

        # -------------------------
        # PARAMETERS
        # -------------------------
        for group in self.context.groups:
            rows.append(Label(f"[{group.name}]", style="class:section"))

            for param in group.params:
                field = TextArea(
                    text=str(param.value),
                    height=1,
                    multiline=False,
                    style="class:input",
                    focusable=True,
                )

                self.inputs.append((param, field))

                row = VSplit([
                    Label(f"-- {param.name}".ljust(30), style="class:label"),
                    field
                ])

                rows.append(row)

            rows.append(Label(""))

        # -------------------------
        # ACTIONS
        # -------------------------
        def on_run():
            self._apply_values()
            self.app.exit(result=self.context)

        def on_exit():
            self.app.exit(result=None)

        run_btn = Button(" RUN ", handler=on_run)
        exit_btn = Button(" EXIT ", handler=on_exit)

        # style classes for buttons
        run_btn.window.style = "class:button-run"
        exit_btn.window.style = "class:button-exit"

        buttons = VSplit(
            [run_btn, exit_btn],
            padding=3
        )

        # -------------------------
        # KEY BINDINGS
        # -------------------------
        kb = KeyBindings()

        @kb.add("tab")
        def _(event):
            event.app.layout.focus_next()

        @kb.add("s-tab")
        def _(event):
            event.app.layout.focus_previous()

        @kb.add("escape")
        def _(event):
            on_exit()

        # -------------------------
        # LAYOUT (MARKDOWN STYLE)
        # -------------------------
        layout = Layout(
            HSplit([
                Label(f"## {self.title}", style="class:title"),
                Label(""),

                Label("### HELP", style="class:section"),
                Label(build_help_text(), style="class:help"),
                Label(""),

                Label("### PARAMETERS", style="class:section"),
                Label(""),
                *rows,

                Label("### PRESETS", style="class:section"),
                Label("(empty)", style="class:dim"),
                Label(""),

                Label("--------------", style="class:footer"),
                buttons,
            ])
        )

        return layout, kb

    def _apply_values(self):
        for param, field in self.inputs:
            param.set(field.text)

    def run(self):
        layout, kb = self._build()

        style = Style.from_dict({
            # titles
            "title": "bold underline",
            "section": "bold",

            # text
            "label": "",
            "help": "italic",
            "dim": "ansigray",
            "footer": "ansigray",

            # inputs
            "input": "bg:#202020 #ffffff",
            "input.focused": "bg:#303060 #ffffff",

            # buttons
            "button-run": "bg:ansigreen #000000 bold",
            "button-exit": "bg:ansired #ffffff bold",
        })

        self.app = Application(
            layout=layout,
            key_bindings=kb,
            full_screen=True,
            mouse_support=True,
            style=style,
        )

        return self.app.run()