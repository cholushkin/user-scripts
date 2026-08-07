import os
from datetime import datetime
from krita import Extension, Krita
from PyQt5.QtCore import QCoreApplication, QTimer

from .ExportCore import export_document


# ============================================================
# Environment Flags
# ============================================================

AUTO_ENV_FLAG = "KRITA_LAYER_EXPORT_AUTO"
OUTPUT_ENV_FLAG = "KRITA_LAYER_EXPORT_OUTPUT"
OBJECTS_ENV_FLAG = "KRITA_LAYER_EXPORT_OBJECTS"
LOG_DIR_ENV_FLAG = "KRITA_LAYER_EXPORT_LOG_DIR"


# ============================================================
# Logging
# ============================================================

def resolve_log_file():
    log_dir = os.environ.get(LOG_DIR_ENV_FLAG)
    if not log_dir:
        return None

    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "krita-export.log")


def log(message):
    log_file = resolve_log_file()
    if not log_file:
        return

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {message}\n")
    except Exception:
        pass


# ============================================================
# Extension
# ============================================================

class LayerExportExtension(Extension):

    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction(
            "layer_export_action",
            "Export Layered Scene",
            "tools/scripts"
        )
        action.triggered.connect(self.manual_export)

    def manual_export(self):
        document = Krita.instance().activeDocument()

        if not document:
            log("Manual export aborted: no active document.")
            return

        log(f"Manual export triggered for: {document.name()}")


# ============================================================
# Safe Shutdown
# ============================================================

def safe_shutdown():
    app = Krita.instance()
    window = app.activeWindow()

    if window:
        log("Closing Krita window.")
        window.close()
    else:
        log("No active window found. Forcing quit.")
        QCoreApplication.quit()


# ============================================================
# Auto Mode
# ============================================================

def try_auto_mode():
    if os.environ.get(AUTO_ENV_FLAG) != "1":
        return

    log("Auto mode detected.")

    output_directory = os.environ.get(OUTPUT_ENV_FLAG)
    objects_raw = os.environ.get(OBJECTS_ENV_FLAG)

    objects = None
    if objects_raw:
        objects = [x.strip() for x in objects_raw.split(",") if x.strip()]

    log(f"Output directory: {output_directory}")
    log(f"Objects: {objects}")

    def check_document():
        document = Krita.instance().activeDocument()

        if not document:
            QTimer.singleShot(200, check_document)
            return

        log(f"Document ready: {document.name()}")

        try:
            export_document(document, output_directory, objects)
            log("Export completed.")
        except Exception as e:
            log(f"Export failed: {e}")

        # Delay shutdown slightly to allow event loop stabilization
        QTimer.singleShot(300, safe_shutdown)

    QTimer.singleShot(200, check_document)


# ============================================================
# Registration
# ============================================================

Krita.instance().addExtension(
    LayerExportExtension(Krita.instance())
)

QTimer.singleShot(0, try_auto_mode)