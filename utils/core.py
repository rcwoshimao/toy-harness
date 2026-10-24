# core.py
import logging
import platform
import os
from dotenv import load_dotenv
import anthropic

import json 
import copy 
from rich.console import Console
from rich.theme import Theme
from rich.markdown import Markdown
from rich.panel import Panel
from rich.markup import escape

console = console = Console(theme=Theme({
    "markdown.code": "bold #268bd2",        # inline code：Solarized 蓝色，不要背景
    "markdown.code_block": "#586e75",       # 代码块的底色文字
}))

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
MAX_TOKENS = 5000
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

ENVIRONMENT_PROMPT = (
    "Windows: the bash tool runs through cmd.exe; use cmd.exe syntax, not Unix "
    "Bash or PowerShell syntax"
    if os.name == "nt"
    else "Unix-like: the bash tool runs the system shell"
)

DENY = {"sudo", "su", "chmod", "chown", "kill", "crontab", "dd", "diskutil", "mkfs"}

SAFE = {"ls", "pwd", "cat", "head", "tail", "wc", "echo", "file", "stat",
        "which", "whoami", "date", "uname", "grep", "rg", "find", "git"}

# 有条件安全：命令本身 OK，但带了这些参数就不算安全
UNSAFE_FLAGS = {
    "find": {"-delete", "-exec", "-execdir", "-ok", "-okdir"},
}
SAFE_GIT_SUBCOMMANDS = {"status", "log", "diff", "branch", "show"}
SHELL_METACHARS = ";&|`$<>\n\r"


