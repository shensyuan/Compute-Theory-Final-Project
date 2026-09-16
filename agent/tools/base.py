"""把 Python 函式轉成 Ollama tool 定義並集中註冊。

* :func:`tool_func` — 註冊單一函式。
* :func:`class_tool_decorator_generator` — 為某個 class 產生一組 (decorator, builder)，
  decorator 標記要註冊的方法，builder 在有實例後把 bound method 註冊進去，
  工具名稱格式為 ``ClassName.method_name``。
"""

from functools import wraps
from inspect import signature
from typing import Any, Callable, TypeVar

from ollama import Tool, _utils
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

tool_list: list[Tool] = []
func_map: dict[str, Callable] = {}
_class_func_data: dict[str, list[Callable]] = {}

T = TypeVar("T")


def _convert_function_to_tool(func: Callable) -> Tool:
    """呼叫 ollama 內建的轉換器，並補上 ``pydantic.Field(description=...)`` 提供的參數說明。"""
    tool = _utils.convert_function_to_tool(func=func)

    if tool.function.parameters is None or tool.function.parameters.properties is None:
        return tool

    func_parameters = signature(func).parameters
    for key, data in tool.function.parameters.properties.items():
        if data.description:
            continue

        parameter = func_parameters.get(key)
        if parameter is None:
            continue

        if isinstance(parameter.default, FieldInfo):
            data.description = parameter.default.description or ""
        elif hasattr(parameter.annotation, "__metadata__"):
            # typing.Annotated[type, Field(...)]
            for meta in parameter.annotation.__metadata__:
                if isinstance(meta, FieldInfo):
                    data.description = meta.description or ""
                    break
    return tool


def _with_resolved_defaults(func: Callable) -> Callable:
    """讓以 ``pydantic.Field(default, ...)`` 當預設值的參數在被省略時拿到真正的 default。

    直接呼叫這種函式時，Python 會把 ``FieldInfo`` 物件本身當成參數值傳入；
    這個包裝器把它換成 ``FieldInfo.default``，而 ``Field(...)``（必填）被省略時則明確拋出 TypeError。
    """
    field_params = {
        name: parameter.default
        for name, parameter in signature(func).parameters.items()
        if isinstance(parameter.default, FieldInfo)
    }
    if not field_params:
        return func

    @wraps(func)
    def wrapper(*args, **kwargs):
        for name, field in field_params.items():
            if name in kwargs:
                continue
            if field.default is PydanticUndefined:
                raise TypeError(f"{func.__name__}() missing required argument: '{name}'")
            kwargs[name] = field.default
        return func(*args, **kwargs)

    return wrapper


def tool_func(func: T) -> T:
    """Decorator：把單一函式註冊為工具。"""
    if not callable(func):
        return func

    tool = _convert_function_to_tool(func=func)
    tool_list.append(tool)
    func_map[tool.function.name] = _with_resolved_defaults(func)
    return func


def class_tool_decorator_generator(class_name: str) -> tuple[Callable[[T], T], Callable[[Any], None]]:
    """回傳 ``(decorator, builder)``。

    用法::

        decorator, builder = class_tool_decorator_generator("MyTools")

        class MyTools:
            @decorator
            def do_something(self, ...): ...

        builder(MyTools())
    """

    def wrapper(func: T) -> T:
        if not callable(func):
            return func
        _class_func_data.setdefault(class_name, []).append(func)
        return func

    def build(instance: Any) -> None:
        pending = _class_func_data.pop(class_name, None)
        if pending is None:
            return

        instance_name = type(instance).__name__

        for func in pending:
            bound_method = getattr(instance, func.__name__)
            tool = _convert_function_to_tool(func=bound_method)
            tool.function.name = f"{instance_name}.{func.__name__}"
            tool_list.append(tool)
            func_map[tool.function.name] = _with_resolved_defaults(bound_method)

    return wrapper, build
