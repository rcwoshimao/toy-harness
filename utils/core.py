# core.py
import logging
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
