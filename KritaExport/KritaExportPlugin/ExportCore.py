import os
import json
import re

from PyQt5.QtGui import QImage


_logger = None


# ============================================================
# Logging
# ============================================================

def set_logger(logger_func):
    global _logger
    _logger = logger_func


def log(msg):
    if _logger:
        _logger(msg)


# ============================================================
# Name Utilities
# ============================================================

def sanitize_name(name):
    name = re.sub(r'\s*\[.*?\]', '', name)  # remove directive blocks
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip("_")


def clean_layer_name(name):
    return re.sub(r'\s*\[.*?\]', '', name).strip()


# ============================================================
# Directive Parsing
# ============================================================

def parse_layer_directives(name):
    matches = re.findall(r'\[(.*?)\]', name)
    if not matches:
        return None

    settings = {
        "export": False,
        "merge": False,
        "crop": False,
        "margins": (0, 0, 0, 0)
    }

    for block in matches:
        token = block.strip()

        if token == "e":
            settings["export"] = True

        elif token == "m":
            settings["merge"] = True

        elif token.startswith("c"):
            settings["crop"] = True

            if ":" in token:
                try:
                    _, value = token.split(":", 1)
                    parts = value.split(",")
                    if len(parts) == 4:
                        settings["margins"] = tuple(int(p.strip()) for p in parts)
                except Exception:
                    log(f"Failed parsing crop margins in {name}")

    if not settings["export"]:
        return None

    return settings


# ============================================================
# Node Utilities
# ============================================================

def is_group(node):
    return node.type() == "grouplayer"


def is_exportable(node):
    return node.type() in ("paintlayer", "grouplayer")


# ============================================================
# Rendering
# ============================================================

def render_node_to_image(node, doc):
    width = doc.width()
    height = doc.height()

    if node.type() == "paintlayer":
        pixel_data = node.pixelData(0, 0, width, height)
    else:
        pixel_data = node.projectionPixelData(0, 0, width, height)

    image = QImage(pixel_data, width, height, QImage.Format_ARGB32)
    return image.copy()


# ============================================================
# Cropping
# ============================================================

def compute_auto_crop(image):
    rect = image.rect()

    min_x = rect.width()
    min_y = rect.height()
    max_x = -1
    max_y = -1

    for y in range(rect.height()):
        for x in range(rect.width()):
            if image.pixelColor(x, y).alpha() > 0:
                if x < min_x: min_x = x
                if y < min_y: min_y = y
                if x > max_x: max_x = x
                if y > max_y: max_y = y

    if max_x == -1:
        return None

    return (min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)


def apply_margins(x, y, w, h, margins, max_w, max_h):
    left, top, right, bottom = margins

    x = max(0, x - left)
    y = max(0, y - top)

    w = w + left + right
    h = h + top + bottom

    if x + w > max_w:
        w = max_w - x

    if y + h > max_h:
        h = max_h - y

    return x, y, w, h


# ============================================================
# Image Export
# ============================================================

def export_image_node(node, doc, output_dir, filename, settings):
    image = render_node_to_image(node, doc)

    if settings["crop"]:
        crop_rect = compute_auto_crop(image)
        if crop_rect is None:
            return None

        x, y, w, h = crop_rect
        x, y, w, h = apply_margins(
            x, y, w, h,
            settings["margins"],
            image.width(),
            image.height()
        )

        image = image.copy(x, y, w, h)
    else:
        x, y = 0, 0
        w = image.width()
        h = image.height()

    image_path = os.path.join(output_dir, filename)
    image.save(image_path, "PNG")

    return {
        "x": x,
        "y": y,
        "width": w,
        "height": h
    }


# ============================================================
# Core Export
# ============================================================

def export_document(document, output_directory, objects=None):
    """
    Entry point for exporting a Krita document.

    Parameters:
        document: Krita document instance
        output_directory: target directory for export
        objects: optional list of object names to export
    """

    log("Starting export_document")

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    doc_name_clean = sanitize_name(document.name())

    root_json = {
        "version": 1,
        "format": "layeredimage",
        "document": {
            "width": document.width(),
            "height": document.height()
        },
        "root": {
            "name": document.name(),
            "type": "group",
            "children": []
        }
    }

    root_node = document.rootNode()

    for node in reversed(root_node.childNodes()):
        try:
            process_node(
                node,
                document,
                output_directory,
                root_json["root"],
                doc_name_clean,
                objects
            )
        except Exception as e:
            log(f"Error processing node {node.name()}: {e}")

    json_path = os.path.join(output_directory, f"{doc_name_clean}.layeredimage")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(root_json, f, indent=4)

    log("Export completed")


def process_node(node, doc, output_dir, parent_json, parent_path, objects=None):
    if not is_exportable(node):
        return

    clean_name = clean_layer_name(node.name())

    # Object filtering (only at root level)
    if objects:
        if parent_json["type"] == "group" and parent_path.count("_") == 0:
            if clean_name not in objects:
                return

    settings = parse_layer_directives(node.name())

    node_name_clean = sanitize_name(node.name())
    current_path = f"{parent_path}_{node_name_clean}"

    if settings:
        if is_group(node) and not settings["merge"]:
            group_json = {
                "name": clean_name,
                "type": "group",
                "children": []
            }

            parent_json["children"].append(group_json)

            for child in reversed(node.childNodes()):
                process_node(
                    child,
                    doc,
                    output_dir,
                    group_json,
                    current_path,
                    objects
                )

        else:
            bounds = export_image_node(
                node,
                doc,
                output_dir,
                f"{current_path}.png",
                settings
            )

            if bounds is None:
                return

            parent_json["children"].append({
                "name": clean_name,
                "type": "image",
                "bounds": bounds,
                "image": f"{current_path}.png"
            })

    else:
        # traverse children to find exportable descendants
        for child in reversed(node.childNodes()):
            process_node(
                child,
                doc,
                output_dir,
                parent_json,
                parent_path,
                objects
            )