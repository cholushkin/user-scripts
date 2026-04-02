# Shared/im_param_binder.py

from dearpygui import dearpygui as dpg


class ImParamBinder:
    def __init__(self, context, logger):
        self.context = context
        self.logger = logger
        self.tag_map = {}

    # -------------------------
    # RENDER
    # -------------------------
    def render(self):
        for group in self.context.groups:
            dpg.add_text(f"[{group.name}]", color=(150, 150, 150))

            for p in group.params:
                tag = self._make_tag(p.name)
                self.tag_map[p.name] = tag

                self._render_param(p, tag)

    def _make_tag(self, name: str) -> str:
        return f"param::{name}"

    def _render_param(self, p, tag):
        val = p.value

        try:
            if p.hints:
                self._render_with_hints(p, tag, val)

            elif p.type == bool:
                dpg.add_checkbox(
                    label=p.name,
                    default_value=bool(val),
                    tag=tag
                )

            elif p.type == int:
                dpg.add_input_int(
                    label=p.name,
                    default_value=int(val),
                    tag=tag
                )

            else:
                dpg.add_input_text(
                    label=p.name,
                    default_value="" if val is None else str(val),
                    tag=tag
                )

        except Exception as e:
            self.logger.error(f"[UI] Failed to render param {p.name}: {e}")

    def _render_with_hints(self, p, tag, val):
        if isinstance(p.hints, dict):
            items = list(p.hints.keys())
            current = next(
                (k for k, v in p.hints.items() if v == val),
                items[0]
            )

            dpg.add_combo(
                items=items,
                default_value=current,
                label=p.name,
                tag=tag
            )
        else:
            items = [str(x) for x in p.hints]

            dpg.add_combo(
                items=items,
                default_value=str(val),
                label=p.name,
                tag=tag
            )

    # -------------------------
    # SYNC → CONTEXT
    # -------------------------
    def collect(self):
        for group in self.context.groups:
            for p in group.params:
                tag = self.tag_map.get(p.name)

                if not tag or not dpg.does_item_exist(tag):
                    continue

                try:
                    raw = dpg.get_value(tag)

                    if raw == "":
                        raw = None

                    if isinstance(p.hints, dict):
                        raw = p.hints.get(raw, raw)

                    if not p.set(raw):
                        self.logger.warn(f"[UI] Invalid value for {p.name}: {p.error}")

                except Exception as e:
                    self.logger.warn(f"[UI] Invalid value for {p.name}: {e}")

    # -------------------------
    # SYNC → UI
    # -------------------------
    def push_to_ui(self):
        for group in self.context.groups:
            for p in group.params:
                tag = self.tag_map.get(p.name)

                if not tag or not dpg.does_item_exist(tag):
                    continue

                try:
                    value = self._convert_for_ui(p)
                    dpg.set_value(tag, value)

                except Exception as e:
                    self.logger.warn(f"[UI] Failed to set {p.name}: {e}")

    def _convert_for_ui(self, p):
        if isinstance(p.hints, dict):
            for k, v in p.hints.items():
                if v == p.value:
                    return k
            return list(p.hints.keys())[0]

        return "" if p.value is None else p.value