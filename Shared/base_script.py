from typing import List, Dict, Optional
import sys
import os

from context import ScriptContext, ParamGroup
from param import Param
from interactive_app import InteractiveApp


LOG_DEBUG = 10
LOG_INFO = 20
LOG_WARN = 30
LOG_ERROR = 40

LOG_PREFIXES = {
    LOG_DEBUG: "DBG",
    LOG_INFO: "",
    LOG_WARN: "WRN",
    LOG_ERROR: "ERR",
}


class BaseScript:
    def __init__(self):
        groups = self._with_base_groups(self.define_groups())
        self.context = ScriptContext(groups)

        defaults = self.get_defaults()
        for g in self.context.groups:
            for p in g.params:
                if p.name in defaults:
                    p.value = defaults[p.name]

        self._log_file_stream: Optional[object] = None

        self._apply_cli_args()

    # -------------------------
    # ABSTRACT
    # -------------------------
    def define_groups(self) -> List[ParamGroup]:
        raise NotImplementedError

    def run(self, ctx: Dict):
        raise NotImplementedError

    def preview(self, ctx: Dict) -> str:
        return ""

    def get_defaults(self) -> Dict:
        return {}

    # -------------------------
    # BASE PARAMS
    # -------------------------
    def _with_base_groups(self, groups: List[ParamGroup]) -> List[ParamGroup]:
        base_group = ParamGroup("Logging", [
            Param(
                "log_level",
                int,
                LOG_INFO,
                hints={
                    "10 - DEBUG": 10,
                    "20 - INFO": 20,
                    "30 - WARN": 30,
                    "40 - ERROR": 40,
                },
                description="Logging level"
            ),
            Param(
                "log_file",
                str,
                None,
                description="Optional log file path"
            ),
            Param(
                "interactive",
                bool,
                False,
                description="Run in interactive mode"
            ),
        ])
        return groups + [base_group]

    # -------------------------
    # DEBUG
    # -------------------------
    def _debug(self, msg: str):
        try:
            ctx = self.context.to_dict()
            if ctx.get("log_level", LOG_INFO) <= LOG_DEBUG:
                print(f"[DBG] {msg}")
        except Exception:
            print(f"[DBG] {msg}")

    # -------------------------
    # CLI
    # -------------------------
    def _apply_cli_args(self):
        import argparse

        parser = argparse.ArgumentParser()
        param_map = {}

        for g in self.context.groups:
            for p in g.params:
                param_map[p.name] = p
                arg_name = f"--{p.name}"

                if p.type == bool:
                    parser.add_argument(
                        arg_name,
                        dest=p.name,
                        action="store_true",
                        help=p.description or None
                    )
                    parser.add_argument(
                        f"--no-{p.name}",
                        dest=p.name,
                        action="store_false",
                        help=f"Disable {p.description}" if p.description else None
                    )
                    parser.set_defaults(**{p.name: None})
                else:
                    parser.add_argument(
                        arg_name,
                        type=str,
                        default=None,
                        help=p.description or None
                    )

        args, unknown = parser.parse_known_args()
        args = vars(args)

        self._debug(f"sys.argv = {sys.argv}")
        self._debug(f"known args = {args}")
        self._debug(f"unknown args = {unknown}")

        for name, value in args.items():
            if value is None:
                continue

            param = param_map[name]
            if not param.set(value):
                print(f"[ERR] Invalid value for {name}: {value}")

        extra = {}
        i = 0
        while i < len(unknown):
            key = unknown[i]
            val = None

            if i + 1 < len(unknown) and not unknown[i + 1].startswith("--"):
                val = unknown[i + 1]
                i += 2
            else:
                i += 1

            if key == "--cwd":
                extra["cwd"] = val
            elif key == "--selected":
                extra["selected"] = val

        self.context.extra = extra
        self._debug(f"extra context = {extra}")

    # -------------------------
    # LOGGING
    # -------------------------
    def log(self, level: int, message: str):
        ctx = self.context.to_dict()

        if level < ctx.get("log_level", LOG_INFO):
            return

        prefix = LOG_PREFIXES.get(level, str(level))
        line = f"[{prefix}] {message}" if prefix else message

        print(line)

        if self._log_file_stream:
            self._log_file_stream.write(line + "\n")
            self._log_file_stream.flush()

    def log_debug(self, msg): self.log(LOG_DEBUG, msg)
    def log_info(self, msg): self.log(LOG_INFO, msg)
    def log_warn(self, msg): self.log(LOG_WARN, msg)
    def log_error(self, msg): self.log(LOG_ERROR, msg)

    # -------------------------
    # LOG FILE
    # -------------------------
    def _setup_log_file(self, ctx: Dict):
        path = ctx.get("log_file")
        if not path:
            return

        try:
            self._log_file_stream = open(path, "w", encoding="utf-8")
        except Exception as e:
            print(f"[WRN] Failed to open log file: {e}")
            self._log_file_stream = None

    def _teardown_log_file(self):
        if self._log_file_stream:
            self._log_file_stream.close()
            self._log_file_stream = None

    # -------------------------
    # EXECUTION
    # -------------------------
    def execute(self):
        ctx = self.context.to_dict()

        if self._is_left_ctrl_pressed():
            self._set_param("interactive", True)
            ctx = self.context.to_dict()

        if ctx.get("interactive"):
            app = InteractiveApp(self.context, title=self.__class__.__name__)
            result = app.run()

            if result is None:
                return

            ctx = self.context.to_dict()

        self._setup_log_file(ctx)

        try:
            self.log_info(f"Script: {self.__class__.__name__}.py")
            self.log_info("Parameters:")

            for k, v in ctx.items():
                if k == "interactive":
                    continue
                self.log_info(f"  {k} = {v}")

            self.log_info("Output:")

            result = self.run(ctx)

            if result is not None:
                self.log_info(str(result))

        finally:
            self._teardown_log_file()

    # -------------------------
    # UTILS
    # -------------------------
    def _set_param(self, name: str, value):
        for g in self.context.groups:
            for p in g.params:
                if p.name == name:
                    p.value = value
                    return

    def _is_left_ctrl_pressed(self) -> bool:
        if os.name != "nt":
            return False

        try:
            import ctypes
            return (ctypes.windll.user32.GetAsyncKeyState(0xA2) & 0x8000) != 0
        except Exception:
            return False