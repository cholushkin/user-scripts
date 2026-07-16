# Shared/im_app.py

import os
from im_logger import ImLogger
from im_presets import ImPresets
from im_param_binder import ImParamBinder
from im_ui import ImUI
from domain_utils import find_project_domain


class ImApp:
    def __init__(self, context, title="Interactive"):
        self.context = context
        self.title = title

        # 1. Initialize core utilities
        self.logger = ImLogger()
        self.binder = ImParamBinder(context, self.logger)

        # 2. Discover Project Domain (.uscript or .uscripts)
        # We check multiple potential sources for a path in order of relevance:
        extra = getattr(context, "extra", {})
        ctx_dict = context.to_dict()
        
        candidate_paths = [
            extra.get("cwd"),             # 1st priority: Explicit working directory from CLI
            ctx_dict.get("path"),         # 2nd priority: A 'path' parameter defined by the script
            extra.get("selected"),        # 3rd priority: Selected file/folder from Double Commander
            os.getcwd()                   # Fallback: Current terminal execution directory
        ]

        project_name, uscript_dir = None, None
        for path_hint in candidate_paths:
            if path_hint:
                project_name, uscript_dir = find_project_domain(str(path_hint))
                if uscript_dir:
                    break  # Stop searching as soon as we find a valid domain!

        # 3. Initialize Global Presets (Baseline)
        self.presets = ImPresets(
            context=context,
            logger=self.logger,
            target_dir=None,
            scope_name="Global"
        )

        # 4. Initialize Project Presets (if domain was discovered)
        self.project_presets = None
        if uscript_dir:
            self.logger.info(f"[DOMAIN] Discovered project '{project_name}' at: {uscript_dir}")
            self.project_presets = ImPresets(
                context=context,
                logger=self.logger,
                target_dir=uscript_dir,
                scope_name=project_name
            )
        else:
            self.logger.info("[DOMAIN] No project domain (.uscript) found in execution path.")

        # 5. Build and attach UI
        ui_title = f"{title} - {project_name}" if project_name else title
        self.ui = ImUI(
            context=context,
            logger=self.logger,
            presets=self.presets,
            binder=self.binder,
            project_presets=self.project_presets,
            project_name=project_name,
            title=ui_title
        )

    # -------------------------
    # RUN
    # -------------------------
    def run(self):
        try:
            return self.ui.run()

        except Exception as e:
            # Critical fallback: log crash before bubbling up
            self.logger.error(f"[CRASH] {e}")
            raise

        finally:
            self.logger.close()