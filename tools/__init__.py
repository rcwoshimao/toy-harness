from tools import bash, eat, read, write 

_MODULES = [bash, eat, read, write]

TOOLS = [m.SCHEMA for m in _MODULES]                 # 传给 API
HANDLERS = {m.SCHEMA["name"]: m for m in _MODULES}   # 名字 → 工具文件