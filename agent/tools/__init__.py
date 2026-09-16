"""Tool 註冊套件。

匯入本套件時會自動載入目錄下所有工具模組（``base`` 與 ``database`` 除外），
每個模組在載入時透過 :func:`base.tool_func` 或 :func:`base.class_tool_decorator_generator`
把自己註冊進 :data:`tool_list` / :data:`func_map`。
"""

from importlib import import_module
from pkgutil import iter_modules

from .base import func_map, tool_list

_NON_TOOL_MODULES = {"base", "database"}

for module_info in iter_modules(__path__):
    if module_info.name in _NON_TOOL_MODULES:
        continue
    import_module(f"{__name__}.{module_info.name}")

__all__ = ["tool_list", "func_map"]
