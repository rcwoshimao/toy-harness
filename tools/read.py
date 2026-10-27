from utils.core import *
from pathlib import Path
from tools.path_policy import check_read, resolve_path
import time 

log = get_logger(__name__)
log.debug(f"STARTED. IN {os.getcwd()}")

MAX_CHARS = 20_000

SCHEMA = {
    "name": "read",
    "description": "Read a text file and return its contents. Use this instead of cat/head/tail.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path of the file to read.",
            }
        },
        "required": ["path"],
    },
}

def run(path):
    console.print(Panel(path, title="read", border_style="yellow")) 
    p = resolve_path(path)

    if not p.exists():
        return f"Error: '{path}' does not exist."
    if p.is_dir():
        return f"Error: '{path}' is a directory, not a file."
    
    try: 
        f = p.read_text(encoding="utf-8")
        if len(f) > MAX_CHARS:
            total = len(f)
            f = f[:MAX_CHARS]
            f += f"\n\n[truncated: showing first {MAX_CHARS} of {total} characters]"
        return f 
    except UnicodeDecodeError as e :
        return f"Error: '{path}' file is not a readable format."
    except PermissionError as e :
        return f"Error: You do not have the permission to access '{path}'."
    except OSError as e:
        return f"Error: cannot read '{p}', {e}"

def check(input):
    return check_read(input.get("path"))
    
                
        
