# Shared/im_app.py

from im_logger import ImLogger
from im_presets import ImPresets
from im_param_binder import ImParamBinder
from im_ui import ImUI


class ImApp:
    def __init__(self, context, title="Interactive"):
        self.context = context
        self.title = title

        # core components
        self.logger = ImLogger()
        self.presets = ImPresets(context, self.logger)
        self.binder = ImParamBinder(context, self.logger)

        self.ui = ImUI(
            context=context,
            logger=self.logger,
            presets=self.presets,
            binder=self.binder,
            title=title
        )

    # -------------------------
    # RUN
    # -------------------------
    def run(self):
        try:
            result = self.ui.run()
            return result

        except Exception as e:
            # critical fallback: log crash
            self.logger.error(f"[CRASH] {e}")
            raise

        finally:
            self.logger.close()