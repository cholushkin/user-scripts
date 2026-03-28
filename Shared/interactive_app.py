from prompt_toolkit import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, VSplit, FloatContainer, Float
from prompt_toolkit.widgets import Label, TextArea, Button, Dialog
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style


LINE = "─" * 60


def build_param_help(context):
    lines = []
    for group in context.groups:
        lines.append(f"[{group.name}]")
        for p in group.params:
            line = f"-- {p.name} ({p.type.__name__}) = {p.default}"
            if p.description:
                line += f"\n   {p.description}"
            lines.append(line)
        lines.append("")
    return "\n".join(lines)


def build_nav_help():
    return "\n".join([
        "Navigation",
        "",
        "Tab / Shift+Tab  - move between fields",
        "Up / Down        - move between fields",
        "Mouse click      - focus field or button",
        "Enter            - activate button",
        "Esc              - exit",
        "",
        "Ctrl+L           - refresh screen",
    ])


class InteractiveApp:
    def __init__(self, context, title="Script"):
        self.context = context
        self.title = title
        self.inputs = []
        self.root_container = None

    def _build(self):
        rows = []

        max_len = max(len(p.name) for g in self.context.groups for p in g.params)
        label_width = max_len + 4

        for group in self.context.groups:
            rows.append(Label(f"[{group.name}]", style="class:group"))

            for param in group.params:
                field = TextArea(
                    text=str(param.value),
                    height=1,
                    multiline=False,
                    focusable=True,
                    style="class:input",
                )

                self.inputs.append((param, field))

                rows.append(
                    VSplit([
                        Label(
                            f"-- {param.name}".ljust(label_width),
                            width=label_width,
                        ),
                        field,
                    ])
                )

            rows.append(Label(""))

        def on_run():
            self._apply_values()
            self.app.exit(result=self.context)

        def on_exit():
            self.app.exit(result=None)

        def show_help():
            dialog = Dialog(
                title="Navigation",
                body=Label(build_nav_help()),
                buttons=[Button("OK", handler=close_dialog)],
                width=50,
            )
            self.root_container.floats.append(Float(content=dialog))

        def close_dialog():
            if self.root_container.floats:
                self.root_container.floats.pop()

        nav_btn = Button("NAV HELP", handler=show_help)
        run_btn = Button("RUN", handler=on_run)
        exit_btn = Button("EXIT", handler=on_exit)

        nav_btn.window.style = "class:button-nav"
        run_btn.window.style = "class:button-run"
        exit_btn.window.style = "class:button-exit"

        buttons = VSplit([nav_btn, run_btn, exit_btn], padding=3)

        kb = KeyBindings()

        @kb.add("tab")
        def _(event):
            event.app.layout.focus_next()

        @kb.add("s-tab")
        def _(event):
            event.app.layout.focus_previous()

        @kb.add("down")
        def _(event):
            event.app.layout.focus_next()

        @kb.add("up")
        def _(event):
            event.app.layout.focus_previous()

        @kb.add("escape")
        def _(event):
            on_exit()

        @kb.add("c-l")
        def _(event):
            event.app.invalidate()

        content = HSplit([
            Label(f"## {self.title}", style="class:title"),
            Label(""),

            Label("### HELP", style="class:section"),
            Label(LINE, style="class:line"),
            Label(build_param_help(self.context)),
            Label(""),

            Label("### PARAMETERS", style="class:section"),
            Label(LINE, style="class:line"),
            *rows,

            Label("### PRESETS", style="class:section"),
            Label(LINE, style="class:line"),
            Label("(empty)", style="class:dim"),
            Label(""),

            Label(LINE, style="class:line"),
            buttons,
        ])

        self.root_container = FloatContainer(content=content, floats=[])

        return Layout(self.root_container), kb

    def _apply_values(self):
        for param, field in self.inputs:
            param.set(field.text)

    def run(self):
        layout, kb = self._build()

        style = Style.from_dict({
            "title": "bold",
            "section": "bold",
            "group": "bold",
            "line": "ansigray",
            "dim": "ansigray",

            "input": "bg:#202020 #aaaaaa",
            "input.focused": "bg:#6060cc #ffffff",

            "button-nav": "bg:ansiblue #ffffff",
            "button-run": "bg:ansigreen #000000 bold",
            "button-exit": "bg:ansired #ffffff bold",
        })

        self.app = Application(
            layout=layout,
            key_bindings=kb,
            full_screen=False,
            mouse_support=True,
            style=style,
            refresh_interval=0.5,
        )

        return self.app.run()