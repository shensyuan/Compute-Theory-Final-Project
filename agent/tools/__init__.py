from .base import tool_list, func_map
from os import listdir

for file_name in listdir(__path__[0]):
    if not file_name.endswith(".py"):
        continue
    if file_name.startswith("__init__.py"):
        continue
    if file_name.startswith("base.py"):
        continue

    __import__(file_name.removesuffix(".py"), globals(), locals(), [__package__], 1)
