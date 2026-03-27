# shared/context.py

from typing import List, Dict
from param import Param


class ParamGroup:
    def __init__(self, name: str, params: List[Param]):
        self.name = name
        self.params = params

    def get_visible(self, context: dict) -> List[Param]:
        return [p for p in self.params if p.is_visible(context)]

    def reset(self):
        for p in self.params:
            p.reset()


class ScriptContext:
    def __init__(self, groups: List[ParamGroup]):
        self.groups = groups

    # -------------------------
    # ACCESS
    # -------------------------

    def to_dict(self) -> Dict:
        result = {}
        for g in self.groups:
            for p in g.params:
                result[p.name] = p.value
        return result

    def get(self, name: str):
        return self.to_dict().get(name)

    # -------------------------
    # STATE
    # -------------------------

    def reset(self):
        for g in self.groups:
            g.reset()

    def visible_groups(self) -> List[ParamGroup]:
        ctx = self.to_dict()
        return [
            ParamGroup(
                g.name,
                [p for p in g.params if p.is_visible(ctx)]
            )
            for g in self.groups
        ]