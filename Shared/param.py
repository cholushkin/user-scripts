# shared/param.py

from typing import Any, Callable, List, Optional


class Param:
    def __init__(
        self,
        name: str,
        type_: type,
        default: Any = None,
        label: Optional[str] = None,
        hints: Optional[List[Any]] = None,
        visible_if: Optional[Callable[[dict], bool]] = None,
        validate: Optional[Callable[[Any], tuple[bool, str]]] = None,
    ):
        self.name = name
        self.type = type_
        self.default = default
        self.value = default
        self.label = label or name
        self.hints = hints or []
        self.visible_if = visible_if
        self.validate_fn = validate

        self.error: Optional[str] = None

    # -------------------------
    # VALUE HANDLING
    # -------------------------

    def set(self, raw_value: Any) -> bool:
        try:
            casted = self.type(raw_value)
        except Exception:
            self.error = f"Invalid type ({self.type.__name__})"
            return False

        if self.validate_fn:
            ok, msg = self.validate_fn(casted)
            if not ok:
                self.error = msg
                return False

        self.value = casted
        self.error = None
        return True

    def reset(self):
        self.value = self.default
        self.error = None

    # -------------------------
    # STATE
    # -------------------------

    def is_visible(self, context: dict) -> bool:
        if not self.visible_if:
            return True
        try:
            return self.visible_if(context)
        except Exception:
            return True

    def to_dict(self):
        return {self.name: self.value}