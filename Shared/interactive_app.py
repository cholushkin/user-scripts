# -------------------------
# CONFIG
# -------------------------
APP_PADDING = (1, 2)
LABEL_WIDTH = 40
INPUT_MIN_WIDTH = 20

# -------------------------
# IMPORTS
# -------------------------
from textual.app import App, ComposeResult
from textual.widgets import Static, Input, Button
from textual.containers import Horizontal
from textual.screen import Screen

# -------------------------
# HELP BUILDER
# -------------------------
def build_help_text(context):
    lines = []

    lines.append("### HELP")
    lines.append("agenda: --Parameter (type) = Default value | description")
    lines.append("")

    for group in context.groups:
        for p in group.params:
            desc = f" | {p.description}" if p.description else ""
            lines.append(f"-- {p.name} ({p.type.__name__}) = {p.default}{desc}")

    return "\n".join(lines)


# -------------------------
# PARAM EDITOR
# -------------------------
class ParamEditor(Horizontal):
    def __init__(self, param):
        super().__init__()
        self.param = param
        self.input = Input(value=str(param.value), id=param.name)

    def compose(self) -> ComposeResult:
        label = f"-- {self.param.name}"
        yield Static(label, classes="param-label")
        yield self.input

    def get_value(self):
        return self.input.value


# -------------------------
# SCREEN
# -------------------------
class InteractiveScreen(Screen):
    def __init__(self, context):
        super().__init__()
        self.context = context
        self.editors = []

    def compose(self) -> ComposeResult:
        # -------------------------
        # TITLE
        # -------------------------
        yield Static(f"## {self.app.title}")
        yield Static("")

        # -------------------------
        # HELP
        # -------------------------
        yield Static(build_help_text(self.context))
        yield Static("")

        # -------------------------
        # CURRENT PARAMETERS
        # -------------------------
        yield Static("### Current parameters")
        yield Static("")

        for group in self.context.groups:
            for param in group.params:
                editor = ParamEditor(param)
                self.editors.append(editor)
                yield editor

        yield Static("")

        # -------------------------
        # PRESETS (EMPTY)
        # -------------------------
        yield Static("### Presets")
        yield Static("(not implemented yet)")
        yield Static("")

        # -------------------------
        # ACTIONS
        # -------------------------
        yield Static("-------")

        yield Horizontal(
            Button("RUN", id="run"),
            Button("EXIT", id="exit"),
        )

    # -------------------------
    # EVENTS
    # -------------------------
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "run":
            self.apply_values()
            self.app.exit(result=self.context)

        elif event.button.id == "exit":
            self.app.exit(result=None)

    # -------------------------
    # APPLY VALUES
    # -------------------------
    def apply_values(self):
        for editor in self.editors:
            param = editor.param
            raw = editor.get_value()
            param.set(raw)


# -------------------------
# APP
# -------------------------
class InteractiveApp(App):
    def __init__(self, context, title="Script"):
        super().__init__()
        self.context = context
        self.title = title
        self.CSS = self._build_css()

    def _build_css(self):
        pad_v, pad_h = APP_PADDING
        return f"""
        Screen {{
            padding: {pad_v} {pad_h};
        }}

        Horizontal {{
            width: 100%;
            height: auto;
        }}

        .param-label {{
            width: {LABEL_WIDTH};
        }}

        Input {{
            width: 1fr;
            min-width: {INPUT_MIN_WIDTH};
        }}

        Button {{
            margin-right: 1;
        }}
        """

    def on_mount(self):
        self.push_screen(InteractiveScreen(self.context))