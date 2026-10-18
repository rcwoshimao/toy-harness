# core.py
import logging
import platform
import os
from dotenv import load_dotenv
import anthropic

import json 
import copy 

load_dotenv()

logging.basicConfig(
    level=logging.WARNING,  # libraries: only warnings and errors
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(os.getenv("LOG_LEVEL", "DEBUG"))  # your code: full debug
    return logger

CLIENT = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")
MAX_TOKENS = 1024
messages = []

os_name = platform.system()          # Mac 上是 "Darwin"，Linux 是 "Linux"，Windows 是 "Windows"
if os_name == "Darwin":
    os_name = f"macOS {platform.mac_ver()[0]}"   # 例如 "macOS 15.1"

shell = os.environ.get("SHELL", "unknown")       # 例如 "/bin/zsh"
cwd = os.getcwd()                                # 例如 "/Users/rebeccachen/Desktop/toy-harness"

SYSTEM_PROMPT = (
    f"You are running on {os_name} with shell {shell}. "
    f"The current working directory is {cwd}. "
    "When searching for files, look in the current directory first."
)
