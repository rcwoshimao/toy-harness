from utils.core import *
from tools.path_policy import check_write, resolve_path


log = get_logger(__name__)
log.debug(f"STARTED. IN {os.getcwd()}")

SCHEMA = {
    "name": "write",
    "description": (
        "Create a new file, or completely overwrite an existing file with the given content. Parent folders are created if needed. Use this instead of echo/cat > in bash."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path of the file to write.",
            },
            "content":{
                "type": "string",
                "description": "The full content of the file to write",
            }
        },
        "required": ["path", "content"],
    },
}

def check(input):
    return check_write(input.get("path"),input.get("content"))

def run(path, content):
    console.print(Panel(path, title="write", border_style="yellow")) 
    p = resolve_path(path)
    existed = p.exists()
    if p.is_dir():
        return f"Error: '{path}' is a directory, not a file."
    try: 
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    except PermissionError as e :
        return f"Error: You do not have the permission to access '{path}'."
    except OSError as e:
        return f"Error: cannot write '{p}', {e}"

    return f"{'Overwrote' if existed else 'Created'} {path} ({len(content)} chars)"


