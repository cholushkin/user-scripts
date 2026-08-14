"""
TODO / Ideas:
- Add multiprocessing/threading support for batch-processing large directories.
- Implement an option to preserve or strip EXIF metadata for JPEGs.
- Add dry-run mode to output the planned conversions without writing to disk.
- Support AVIF output format for better modern web compression.
"""

import sys
import os
from pathlib import Path

# Ensure the 'Shared' framework module is importable
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../Shared")
))

from base_script import BaseScript
from context import ParamGroup
from param import Param

from PIL import Image

# Optional dependency for SVG rasterization
try:
    import cairosvg
    HAS_CAIROSVG = True
except ImportError:
    HAS_CAIROSVG = False


DEFAULTS = {
    "log_level": 20,
    "log_file": None,
    "paths": "",
    "recursive": False,
    "scale": 0.5,
    "width": 0,
    "height": 0,
    "keep_aspect": True,
    "output_dir": ".",
    "format": "jpg",
    "quality": 60,
    "overwrite": False,
}

SUPPORTED_OUTPUT_FORMATS = ("jpg", "webp", "png")

SUPPORTED_FORMATS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tiff",
    ".webp",
    ".svg"
)


class ImageResizeScript(BaseScript):

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
                Param(
                    "format",
                    str,
                    DEFAULTS["format"],
                    label="Output format",
                    description="jpg, webp, or png (SVGs always save as png)"
                ),
                Param("quality", int, DEFAULTS["quality"]),
                Param("overwrite", bool, DEFAULTS["overwrite"]),
            ]),
        ]

    def get_defaults(self):
        return DEFAULTS

    def preview(self, ctx):
        return f"Resize images → {ctx['output_dir']} ({ctx['format']})"

    def parse_paths(self, paths_str):
        return [p.strip() for p in paths_str.split(";") if p.strip()]

    def collect_images(self, paths, recursive):
        files = []
        for path in paths:
            p = Path(path)
            if p.is_file() and p.suffix.lower() in SUPPORTED_FORMATS:
                files.append(p)
            elif p.is_dir():
                glob_pattern = "*.*" if not recursive else "**/*.*"
                files.extend(
                    f for f in p.glob(glob_pattern)
                    if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS
                )
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
                return img.resize((width or ow, height or oh), Image.LANCZOS)

        return img.resize((int(ow * scale), int(oh * scale)), Image.LANCZOS)

    def process_image(self, path, output_dir, ctx):
        try:
            # SVGs require specialized rasterization via cairosvg
            if path.suffix.lower() == ".svg":
                if not HAS_CAIROSVG:
                    self.log_error(f"Cannot process {path}: 'cairosvg' is not installed. Run 'pip install cairosvg'.")
                    return

                output_path = output_dir / f"{path.stem}.png"

                if output_path.exists() and not ctx["overwrite"]:
                    self.log_warn(f"Skip exists: {output_path}")
                    return

                output_dir.mkdir(parents=True, exist_ok=True)

                w = ctx["width"]
                h = ctx["height"]
                kwargs = {}
                
                # Apply explicit dimensions if provided, bypassing scale for exact rasterization
                if w > 0: kwargs["output_width"] = w
                if h > 0: kwargs["output_height"] = h

                self.log_info(f"{path} -> {output_path} (SVG rasterized to PNG)")
                cairosvg.svg2png(url=str(path), write_to=str(output_path), **kwargs)
                return

            img = Image.open(path)
            output_format = ctx["format"].lower()

            if output_format not in SUPPORTED_OUTPUT_FORMATS:
                self.log_error(f"Unsupported output format: {output_format}")
                return

            # Format-specific color mode coercions
            if output_format == "jpg" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            elif output_format == "webp" and img.mode == "P":
                img = img.convert("RGBA")

            img = self.resize_image(img, ctx)
            output_path = output_dir / f"{path.stem}.{output_format}"

            if output_path.exists() and not ctx["overwrite"]:
                self.log_warn(f"Skip exists: {output_path}")
                return

            output_dir.mkdir(parents=True, exist_ok=True)
            self.log_info(f"{path} -> {output_path}")

            if output_format == "jpg":
                img.save(output_path, "JPEG", quality=ctx["quality"], optimize=True, progressive=True)
            elif output_format == "webp":
                img.save(output_path, "WEBP", quality=ctx["quality"], optimize=True)
            elif output_format == "png":
                img.save(output_path, "PNG", optimize=True)

        except Exception as e:
            self.log_error(f"Error processing {path}: {e}")

    def run(self, ctx):
        extra = getattr(self.context, "extra", {})
        paths = []

        # 1. Prioritize reading paths from Double Commander temporary selection files
        selected_file = extra.get("selected")
        if selected_file and Path(selected_file).exists():
            with open(selected_file, "r", encoding="utf-8") as f:
                paths.extend(line.strip() for line in f if line.strip())

        # 2. Fallback to CLI arguments
        if ctx["paths"]:
            paths.extend(self.parse_paths(ctx["paths"]))

        # 3. Fallback to current working directory
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


if __name__ == "__main__":
    ImageResizeScript().execute()