from ollama import Tool, _utils
from pydantic.fields import FieldInfo

from inspect import signature
from typing import Any, Callable, TypeVar

tool_list: list[Tool] = []
func_map: dict[str, Callable] = {}
__class_func_data: dict[str, list[Callable]] = {}

T = TypeVar("T")


def _convert_function_to_tool(func: Callable) -> Tool:
    tool = _utils.convert_function_to_tool(func=func)

    if tool.function.parameters is None:
        return tool
    if tool.function.parameters.properties is None:
        return tool

    func_parameters = signature(func).parameters
    for key, data in tool.function.parameters.properties.items():
        if data.description:
            continue

        parameter = func_parameters.get(key)
        if parameter is None:
            continue

        if type(parameter.default) is FieldInfo:
            data.description = parameter.default.description or ""
        elif hasattr(parameter.annotation, "__metadata__"):
            metadata = parameter.annotation.__metadata__
            try:
                field_info = metadata[0]
                if type(field_info) is not FieldInfo:
                    continue
                data.description = field_info.description or ""
            except:
                pass
    return tool


def tool_func(func: T) -> T:
    if not callable(func):
        return func

    tool = _convert_function_to_tool(func=func)
    tool_list.append(tool)
    func_map[tool.function.name] = func
    return func


def class_tool_decorator_generator(class_name: str) -> tuple[Callable[[T], T], Callable[[Any], None]]:
    def wrapper(func: T) -> T:
        if not callable(func):
            return func

        temp_data = __class_func_data.get(class_name)
        if temp_data is None:
            temp_data = []
            __class_func_data[class_name] = temp_data
        temp_data.append(func)

        return func

    def build(instance: Any):
        temp_data = __class_func_data.get(class_name)
        if temp_data is None:
            return

        try:
            instance_name = instance.__class__.__name__
        except:
            try:
                instance_name = str(instance)
            except:
                instance_name = class_name

        for func in temp_data:
            instance_func = getattr(instance, func.__name__)

            tool = _convert_function_to_tool(func=instance_func)
            tool.function.name = f"{instance_name}.{func.__name__}"
            tool_list.append(tool)
            func_map[tool.function.name] = instance_func

        del __class_func_data[class_name]

    return wrapper, build
