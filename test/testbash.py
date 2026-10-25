# tests/test_bash.py
import pytest
from tools import bash

@pytest.mark.parametrize("command, expected", [
    ("ls",                    "allow"),
    ("ls -la tools",          "allow"),
    ("ls; rm x",              "deny"),
    ("cat a | head",          "deny"),
    ("rm -rf /",              "deny"),
    ("open -a Calculator",    "ask"),
    ("python3 -c 'print(1)'", "ask"),   # 或者 "deny"，看你决定
    ("git status",            "allow"),
    ("git push",              "ask"),
    ("",                      "deny"),
])
def test_check(command, expected):
    decision, reason = bash.check({"command": command})
    assert decision == expected, reason