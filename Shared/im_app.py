# todo:
# - consider abstracting the domain discovery loop into its own factory/builder class if more resolution priorities are added
# ideas:
# - cache discovered uscript_dirs in a temporary dotfile to speed up repeated CLI executions in huge project trees

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

        # 2. Discover Project Domain (.uscript hierarchy & config.json)
        # We check multiple potential sources for a path in order of relevance:
        extra = getattr(context, "extra", {})
        ctx_dict = context.to_dict()
        
        candidate_paths = [
            extra.get("cwd"),             # 1st priority: Explicit working directory from CLI
            ctx_dict.get("path"),         # 2nd priority: A 'path' parameter defined by the script
            extra.get("selected"),        # 3rd priority: Selected file/folder from Double Commander
            os.getcwd()                   # Fallback: Current terminal execution directory
        ]

        project_info = {}
        for path_hint in candidate_paths:
            if path_hint:
                info = find_project_domain(str(path_hint))
                if info and info.get("uscript_dirs"):
                    project_info = info
                    self.logger.info(f"[DOMAIN] Discovery initialized from path hint: {path_hint}")
                    break
        
        project_name = project_info.get("project_name")
        uscript_dirs = project_info.get("uscript_dirs", [])

        # 3. Initialize Global Presets (Baseline)
        self.presets = ImPresets(
            context=context,
            logger=self.logger,
            target_dir=None,
            scope_name="Global"
        )

        # 4. Initialize Hierarchical Local Presets
        self.local_preset_managers = []
        
        if uscript_dirs:
            if project_info.get("root_path"):
                self.logger.info(f"[DOMAIN] Discovered project '{project_name}' (Root: {project_info.get('root_path')})")
            if project_info.get("asset_folder"):
                self.logger.info(f"[DOMAIN] Project Config mapped Unity Asset Folder: '{project_info.get('asset_folder')}'")

            # Reverse the list so the UI renders Top-Down (Root -> Subfolder -> Closest)
            for u_dir in reversed(uscript_dirs):
                # Name the scope after the parent folder of .uscript (e.g., "ArtSources", "TargetOne")
                parent_folder_name = os.path.basename(os.path.dirname(u_dir))
                scope_name = f"[{parent_folder_name}]" if parent_folder_name else "[Local]"
                
                self.logger.info(f"[DOMAIN] Binding Local Presets for {scope_name} at: {u_dir}")
                
                manager = ImPresets(
                    context=context,
                    logger=self.logger,
                    target_dir=u_dir,
                    scope_name=scope_name
                )
                self.local_preset_managers.append(manager)
        else:
            self.logger.info("[DOMAIN] Standalone execution (No .uscript hierarchy found).")

        # 5. Build and attach UI
        ui_title = f"{title} - {project_name}" if project_name else title
        self.ui = ImUI(
            context=context,
            logger=self.logger,
            presets=self.presets,
            binder=self.binder,
            local_preset_managers=self.local_preset_managers, 
            title=ui_title
        )

    # -------------------------
    # RUN
    # -------------------------
    def run(self):
        try:
            return self.ui.run()

        except Exception as e:
            # Critical fallback: log crash before exiting
            self.logger.error(f"UI Crash: {e}")
            return None