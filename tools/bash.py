from utils.core import *
import subprocess
import shlex
import time




log = get_logger(__name__)
log.debug(f"STARTED. IN {os.getcwd()}")

tools = [
    {
        "name": "bash",
        "description": "Run a shell command",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command given to run in shell. Will time out after 30 seconds.",
                }
            },
            "required": ["command"],
        },
    },
    {
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
]

def bash(command, timeout=30):
    console.print(Panel(command, title="bash", border_style="yellow")) 
    start = time.monotonic()
    proc = subprocess.Popen(command, shell=True, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    while True:
        try:
            stdout, stderr = proc.communicate(timeout=1)   # 最多等 1 秒
            break                                          # 跑完了
        except subprocess.TimeoutExpired:
            elapsed = time.monotonic() - start
            if elapsed > timeout:
                proc.kill()
                stdout, stderr = proc.communicate()
                print(f"\r  stopped after {elapsed:.0f}s")
                return f"Command timed out after {timeout} seconds and was stopped."
            print(f"\r  running for {elapsed:.0f}s...", end="", flush=True)

    print(f"\r  done in {time.monotonic() - start:.1f}s        ")
    # TODO: 用 stdout、stderr、proc.returncode 组装要送回给 Claude 的结果
    # " output = bash(command)" 
    returncode = proc.returncode
    if returncode != 0: # This is safer than == 1 
        return f"command failed. \n return code = {returncode}. \n stdout: {stdout}. \n stderr: {stderr}"
    else: 
        return f"command succeed. \n return code = {returncode}. \n stdout: {stdout}. \n stderr: {stderr}"

def eat(number):
    return f"Ate {number} apples."


TOOL_FUNCTIONS={
    "bash": bash,
    "eat": eat,
}

def check_command(command):
    """Return (decision, reason). decision is "allow", "deny", or "ask"."""

    # 1. 先挡串联命令。必须第一步做，不然 "ls; rm x" 会被当成 ls
    found = set(SHELL_METACHARS) & set(command)
    if found:
        chars = ", ".join(sorted(found))
        return "deny", f"contains shell operators ({chars}). Run one simple command at a time"

    # 2. 把命令拆成单词
    try:
        words = shlex.split(command)
    except ValueError:
        return "ask", "could not parse the command"
    if not words:
        return "deny", "empty command"

    program = words[0]
    args = words[1:]

    # 3. 黑名单：直接拒绝
    if program in DENY:
        return "deny", f" '{program}' is never allowed"

    # 4. 不在白名单里：问你
    if program not in SAFE:
        return "ask", f" '{program}' is not in the safe list"

    # 5. 在白名单里，但带了危险参数：问你
    if program in UNSAFE_FLAGS:
        bad = UNSAFE_FLAGS[program] & set(args)
        if bad:
            return "ask", f"'{program}' with {', '.join(sorted(bad))} can change files"

    # 6. git 只放行只读的子命令
    if program == "git":
        if not args or args[0] not in SAFE_GIT_SUBCOMMANDS:
            return "ask", "only read-only git commands are auto-approved"

    return "allow", "known safe command"



