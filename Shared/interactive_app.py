# -------------------------
# CONFIG
# -------------------------
LABEL_WIDTH = 40

# -------------------------
# IMPORTS
# -------------------------
import os

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
        yield Static(f"-- {self.param.name}", classes="param-label")
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
        # TITLE
        yield Static(f"## {self.app.title}")
        yield Static("")

        # HELP
        yield Static(build_help_text(self.context))
        yield Static("")

        # PARAMETERS
        yield Static("### Current parameters")
        yield Static("")

        for group in self.context.groups:
            for param in group.params:
                editor = ParamEditor(param)
                self.editors.append(editor)
                yield editor

        yield Static("")

        # PRESETS
        yield Static("### Presets")
        yield Static("(not implemented yet)")
        yield Static("")

        # ACTIONS
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
            editor.param.set(editor.get_value())


# -------------------------
# APP
# -------------------------
class InteractiveApp(App):
    def __init__(self, context, title="Script"):
        super().__init__()
        self.context = context
        self.title = title

        # load CSS from file
        self.CSS = self._load_css()

    def _load_css(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        css_path = os.path.join(base_dir, "interactive_app.css")

        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                return f.read()

        return ""  # fallback if missing

    def on_mount(self):
        self.push_screen(InteractiveScreen(self.context))