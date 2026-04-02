class InteractiveLogger:
    def __init__(self):
        self.buffer = []
        self.ui_ready = False
        self.ui_callback = None  # function to push logs into UI

    def attach_ui(self, callback):
        self.ui_callback = callback
        self.ui_ready = True
        self.flush()

    def log(self, line: str):
        self.buffer.append(line)
        if self.ui_ready and self.ui_callback:
            self.ui_callback(line)

    def flush(self):
        if not self.ui_ready or not self.ui_callback:
            return
        for line in self.buffer:
            self.ui_callback(line)