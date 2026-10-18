import os
from datetime import datetime
from krita import Extension, Krita
from PyQt5.QtCore import QCoreApplication, QTimer

from .ExportCore import export_document, set_logger

# ============================================================
# Environment Flags
# ============================================================
AUTO_ENV_FLAG = "KRITA_LAYER_EXPORT_AUTO"
JSON_ENV_FLAG = "KRITA_LAYER_EXPORT_JSON"
ROOT_ENV_FLAG = "KRITA_LAYER_EXPORT_ROOT"
ASSETS_ENV_FLAG = "KRITA_LAYER_EXPORT_ASSETS"
OUT_OVERRIDE_ENV_FLAG = "KRITA_LAYER_EXPORT_OUT_OVERRIDE"
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
    if not log_file: return
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {message}\n")
    except Exception:
        pass

# Wire the core logger to this file's log function
set_logger(log)

# ============================================================
# Extension
# ============================================================
class LayerExportExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        pass

Krita.instance().addExtension(LayerExportExtension(Krita.instance()))

def safe_shutdown():
    windows = Krita.instance().windows()
    if len(windows) > 0:
        windows[0].close()
    else:
        log("No Krita window found. Forcing quit.")
        QCoreApplication.quit()

# ============================================================
# Auto Mode
# ============================================================
def try_auto_mode():
    if os.environ.get(AUTO_ENV_FLAG) != "1":
        return

    log("Auto mode detected.")

    out_override = os.environ.get(OUT_OVERRIDE_ENV_FLAG, "")
    json_path = os.environ.get(JSON_ENV_FLAG, "")
    root_path = os.environ.get(ROOT_ENV_FLAG, "")
    assets_path = os.environ.get(ASSETS_ENV_FLAG, "")
    objects_raw = os.environ.get(OBJECTS_ENV_FLAG, "")

    def check_document():
        document = Krita.instance().activeDocument()

        if not document:
            QTimer.singleShot(200, check_document)
            return

        log(f"Document ready: {document.name()}")

        try:
            export_document(document, out_override, json_path, root_path, assets_path, objects_raw)
            log("Export completed.")
        except Exception as e:
            log(f"Export failed: {e}")

        # Delay shutdown slightly to allow event loop stabilization
        QTimer.singleShot(300, safe_shutdown)

    QTimer.singleShot(200, check_document)

try_auto_mode()