from utils.core import *

log = get_logger(__name__)
log.debug(f"STARTED. IN {os.getcwd()}")

SCHEMA={
    "name": "eat",
    "description": "Fake command for you to pretend to have eaten an apple",
    "input_schema": {
        "type": "object",
        "properties": {
            "number": {
                "type": "integer",
                "description": "Number of apples eaten",
            }
        },
        "required": ["number"],
    },
}


def run(number):
    print(f"calling run with {number}")
    return f"Ate {number} apples."


def check(input):
    print("ran check")
    return "allow", "command succeed. Harmless test tool"
