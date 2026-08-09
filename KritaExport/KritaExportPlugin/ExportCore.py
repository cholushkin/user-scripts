import os
import json
import re
from PyQt5.QtGui import QImage

# ============================================================
# Logging Delegate
# ============================================================
_logger = None

def set_logger(logger_func):
    global _logger
    _logger = logger_func

def log(msg):
    if _logger:
        _logger(msg)
    else:
        print(f"[ExportCore] {msg}")

# ============================================================
# Name Utilities & Parsing
# ============================================================
def sanitize_name(name):
    name = re.sub(r'\s*\[.*?\]', '', name)  # remove directive blocks
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip("_")

def clean_layer_name(name):
    return re.sub(r'\s*\[.*?\]', '', name).strip()

def parse_layer_directives(name):
    matches = re.findall(r'\[(.*?)\]', name)
    if not matches:
        return None

    settings = {"export": False, "merge": False, "crop": False, "margins": (0, 0, 0, 0)}

    for match in matches:
        m = match.lower()
        if m == 'e': settings['export'] = True
        elif m == 'm': settings['merge'] = True
        elif m.startswith('c'):
            settings['crop'] = True
            if ':' in m:
                try:
                    parts = [int(p.strip()) for p in m.split(':')[1].split(',')]
                    if len(parts) == 4:
                        settings['margins'] = tuple(parts)
                except ValueError:
                    log(f"Warning: Invalid crop margins in layer '{name}'")
                    
    return settings

# ============================================================
# Krita Tree Navigation & Export
# ============================================================
def is_group(node):
    return node.type() == 'grouplayer'

def find_node_by_name(root, target_name):
    if clean_layer_name(root.name()) == target_name:
        return root
    for child in root.childNodes():
        found = find_node_by_name(child, target_name)
        if found: return found
    return None

def export_image_node(node, doc, output_dir, file_name, settings):
    file_path = os.path.join(output_dir, file_name)

    if settings["crop"]:
        bounds = node.bounds()
        margins = settings.get("margins", (0, 0, 0, 0))
        left, top, right, bottom = margins
        x = max(0, bounds.x() - left)
        y = max(0, bounds.y() - top)
        width = min(doc.width() - x, bounds.width() + left + right)
        height = min(doc.height() - y, bounds.height() + top + bottom)
    else:
        x, y, width, height = 0, 0, doc.width(), doc.height()

    if width <= 0 or height <= 0:
        log(f"Skipping {file_name}: Invalid dimensions ({width}x{height})")
        return None

    img_data = node.projectionPixelData(x, y, width, height)
    qimg = QImage(img_data, width, height, QImage.Format_ARGB32)

    os.makedirs(output_dir, exist_ok=True)
    qimg.save(file_path, "PNG")
    log(f"Exported PNG: {file_name}")

    return {"x": x, "y": y, "width": width, "height": height}

def process_node(node, doc, output_dir, parent_json, parent_path):
    clean_name = clean_layer_name(node.name())
    settings = parse_layer_directives(node.name())
    node_name_clean = sanitize_name(node.name())
    current_path = f"{parent_path}_{node_name_clean}"

    if settings:
        if is_group(node) and not settings.get("merge"):
            group_json = {
                "name": clean_name,
                "type": "group",
                "children": []
            }
            parent_json["children"].append(group_json)

            for child in reversed(node.childNodes()):
                process_node(child, doc, output_dir, group_json, current_path)
        else:
            bounds = export_image_node(node, doc, output_dir, f"{current_path}.png", settings)
            if bounds is None: return

            parent_json["children"].append({
                "name": clean_name,
                "type": "image",
                "bounds": bounds,
                "imagePath": f"{current_path}.png"
            })
    else:
        for child in reversed(node.childNodes()):
            process_node(child, doc, output_dir, parent_json, parent_path)

# ============================================================
# Main Entry
# ============================================================
def export_document(doc, out_override, json_path, root_path, assets_path, objects_raw):
    log(f"Starting export for document: {doc.name()}")

    targets = []
    
    if json_path and os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                targets = data.get("export_parameters", {}).get("objects", [])
        except Exception as e:
            log(f"Failed to parse JSON: {e}")

    if not targets:
        objs = [x.strip() for x in objects_raw.split(",")] if objects_raw else []
        if objs:
            targets = [{"layer": obj, "name": sanitize_name(obj), "subfolder": ""} for obj in objs]
        else:
            targets = [{"layer": doc.rootNode().name(), "name": sanitize_name(doc.rootNode().name()), "subfolder": ""}]

    for target in targets:
        layer_name = target.get("layer", "")
        subfolder = target.get("subfolder", "")
        export_name = target.get("name", sanitize_name(layer_name))

        if out_override:
            target_dir = os.path.join(out_override, subfolder)
        elif root_path and assets_path:
            target_dir = os.path.join(root_path, assets_path, subfolder)
        else:
            target_dir = os.path.join(os.path.dirname(doc.fileName()), subfolder)

        os.makedirs(target_dir, exist_ok=True)
        log(f"Routing '{layer_name}' -> {target_dir}")

        node = find_node_by_name(doc.rootNode(), layer_name)
        if not node:
            log(f"WARN: Could not find target layer '{layer_name}' in document.")
            continue

        manifest = {
            "version": 1,
            "name": export_name,
            "document": {
                "width": doc.width(),
                "height": doc.height()
            },
            "children": []
        }

        process_node(node, doc, target_dir, manifest, export_name)

        manifest_path = os.path.join(target_dir, f"{export_name}.layeredimage")
        with open(manifest_path, 'w', encoding='utf-8') as mf:
            json.dump(manifest, mf, indent=4)
            
        log(f"Saved manifest: {export_name}.layeredimage")