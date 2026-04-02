# Shared/im_logger.py

import os
import sys
from typing import Optional, Callable

LOG_DEBUG = 10
LOG_INFO = 20
LOG_WARN = 30
LOG_ERROR = 40

LOG_PREFIXES = {
    LOG_DEBUG: "DBG",
    LOG_INFO: "",
    LOG_WARN: "WRN",
    LOG_ERROR: "ERR",
}


class ImLogger:
    def __init__(self):
        self.buffer = []
        self.ui_callback: Optional[Callable[[str], None]] = None
        self.ui_ready = False
        self.file = None

        self._setup_file()

    # -------------------------
    # FILE LOG
    # -------------------------
    def _setup_file(self):
        try:
            script_path = os.path.abspath(sys.argv[0])
            script_dir = os.path.dirname(script_path)

            script_name = os.path.splitext(os.path.basename(script_path))[0]
            log_name = f"{script_name}.im_mode.log"

            log_path = os.path.join(script_dir, log_name)

            self.file = open(log_path, "w", encoding="utf-8")

        except Exception:
            self.file = None

    def _write_file(self, line: str):
        if not self.file:
            return
        try:
            self.file.write(line + "\n")
            self.file.flush()
        except Exception:
            pass

    def close(self):
        if self.file:
            try:
                self.file.close()
            except Exception:
                pass
            self.file = None

    # -------------------------
    # UI ATTACH
    # -------------------------
    def attach_ui(self, callback: Callable[[str], None]):
        self.ui_callback = callback
        self.ui_ready = True
        self._flush_to_ui()

    def _flush_to_ui(self):
        if not self.ui_ready or not self.ui_callback:
            return
        for line in self.buffer:
            self.ui_callback(line)

    # -------------------------
    # LOGGING
    # -------------------------
    def log(self, level: int, message: str):
        prefix = LOG_PREFIXES.get(level, "")
        line = f"[{prefix}] {message}" if prefix else message

        self.buffer.append(line)
        self._write_file(line)

        if self.ui_ready and self.ui_callback:
            self.ui_callback(line)

    # convenience
    def debug(self, msg): self.log(LOG_DEBUG, msg)
    def info(self, msg): self.log(LOG_INFO, msg)
    def warn(self, msg): self.log(LOG_WARN, msg)
    def error(self, msg): self.log(LOG_ERROR, msg)

    # -------------------------
    # UTIL
    # -------------------------
    def clear(self):
        self.buffer.clear()