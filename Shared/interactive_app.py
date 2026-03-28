# -------------------------
# CONFIG
# -------------------------

APP_PADDING = (1, 2)

LABEL_WIDTH = 40        # width of label column
INPUT_MIN_WIDTH = 20    # safety minimum

SHOW_PARAM_TYPE = True

HEADER_SEPARATOR = "-" * 60


# -------------------------
# IMPORTS
# -------------------------

from textual.app import App, ComposeResult
from textual.widgets import Static, Input, Button
from textual.containers import Horizontal
from textual.screen import Screen


# -------------------------
# PARAM EDITOR
# -------------------------

class ParamEditor(Horizontal):
    def __init__(self, param):
        super().__init__()
        self.param = param
        self.input = Input(value=str(param.value), id=param.name)

    def compose(self) -> ComposeResult:
        label = self.param.label
        if SHOW_PARAM_TYPE:
            label += f" ({self.param.type.__name__})"

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

        yield Static(f"Script: {self.app.title}")
        yield Static("")

        # -------------------------
        # PARAMS (NATURAL FLOW)
        # -------------------------
        for group in self.context.groups:
            yield Static(f"[{group.name}]")

            for param in group.params:
                editor = ParamEditor(param)
                self.editors.append(editor)
                yield editor

            yield Static("")

        yield Static(HEADER_SEPARATOR)

        # -------------------------
        # ACTIONS
        # -------------------------
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