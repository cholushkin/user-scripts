import sys
import os
from pathlib import Path

# --- match your Shared import pattern ---
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../Shared")
))

from base_script import BaseScript
from context import ParamGroup
from param import Param

from PIL import Image


# -------------------------
# DEFAULTS
# -------------------------
DEFAULTS = {
    "log_level": 20,
    "log_file": None,

    # input
    "paths": "",   # semicolon-separated
    "recursive": False,

    # resize
    "scale": 0.5,
    "width": 0,
    "height": 0,
    "keep_aspect": True,

    # output
    "output_dir": ".",
    "quality": 60,
    "overwrite": False,
}


SUPPORTED_FORMATS = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp")


# -------------------------
# SCRIPT
# -------------------------
class ImageResizeScript(BaseScript):

    # --- framework hooks ---

    def define_groups(self):
        return [
            ParamGroup("Input", [
                Param(
                    "paths",
                    str,
                    DEFAULTS["paths"],
                    label="Input paths",
                    description="Files or folders (semicolon-separated)"
                ),
                Param(
                    "recursive",
                    bool,
                    DEFAULTS["recursive"],
                    label="Recursive",
                    description="Process directories recursively"
                ),
            ]),

            ParamGroup("Resize", [
                Param("scale", float, DEFAULTS["scale"]),
                Param("width", int, DEFAULTS["width"]),
                Param("height", int, DEFAULTS["height"]),
                Param("keep_aspect", bool, DEFAULTS["keep_aspect"]),
            ]),

            ParamGroup("Output", [
                Param("output_dir", str, DEFAULTS["output_dir"]),
                Param("quality", int, DEFAULTS["quality"]),
                Param("overwrite", bool, DEFAULTS["overwrite"]),
            ]),
        ]

    def get_defaults(self):
        return DEFAULTS

    def preview(self, ctx):
        return f"Resize images → {ctx['output_dir']}"

    # -------------------------
    # CORE LOGIC
    # -------------------------

    def parse_paths(self, paths_str):
        return [p.strip() for p in paths_str.split(";") if p.strip()]

    def collect_images(self, paths, recursive):
        files = []

        for path in paths:
            p = Path(path)

            if p.is_file() and p.suffix.lower() in SUPPORTED_FORMATS:
                files.append(p)

            elif p.is_dir():
                if recursive:
                    files.extend(f for f in p.rglob("*") if f.suffix.lower() in SUPPORTED_FORMATS)
                else:
                    files.extend(f for f in p.glob("*") if f.suffix.lower() in SUPPORTED_FORMATS)

        return files

    def resize_image(self, img, ctx):
        ow, oh = img.size

        width = ctx["width"]
        height = ctx["height"]
        scale = ctx["scale"]
        keep_aspect = ctx["keep_aspect"]

        if width or height:
            if keep_aspect:
                img.thumbnail((width or ow, height or oh))
                return img
            else:
                return img.resize(
                    (width or ow, height or oh),
                    Image.LANCZOS
                )

        return img.resize(
            (int(ow * scale), int(oh * scale)),
            Image.LANCZOS
        )

    def process_image(self, path, output_dir, ctx):
        try:
            img = Image.open(path)

            # convert for JPEG
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            img = self.resize_image(img, ctx)

            output_path = output_dir / (path.stem + ".jpg")

            if output_path.exists() and not ctx["overwrite"]:
                self.log_warn(f"Skip exists: {output_path}")
                return

            output_dir.mkdir(parents=True, exist_ok=True)

            self.log_info(f"{path} -> {output_path}")

            img.save(
                output_path,
                "JPEG",
                quality=ctx["quality"],
                optimize=True,
                progressive=True
            )

        except Exception as e:
            self.log_error(f"Error processing {path}: {e}")

    # -------------------------
    # RUN
    # -------------------------
    def run(self, ctx):
        extra = getattr(self.context, "extra", {})

        paths = []

        # 1. Double Commander selection (PRIMARY)
        selected_file = extra.get("selected")
        if selected_file and Path(selected_file).exists():
            with open(selected_file, "r", encoding="utf-8") as f:
                paths.extend(line.strip() for line in f if line.strip())

        # 2. Manual / CLI paths
        if ctx["paths"]:
            paths.extend(self.parse_paths(ctx["paths"]))

        # 3. Fallback (drag-drop / cwd)
        if not paths and "cwd" in extra:
            paths = [extra["cwd"]]

        if not paths:
            self.log_error("No input paths provided")
            return

        images = self.collect_images(paths, ctx["recursive"])

        if not images:
            self.log_warn("No images found")
            return

        output_dir = Path(ctx["output_dir"])

        for img_path in images:
            self.process_image(img_path, output_dir, ctx)

        self.log_info(f"Done. Processed {len(images)} images.")


# -------------------------
# ENTRY POINT
# -------------------------
if __name__ == "__main__":
    ImageResizeScript().execute()