from utils.core import *
import subprocess
import shlex

log = get_logger(__name__)
log.debug("starting")

tool_choice = {"type": "auto"}

tools = [
    {
        "name": "bash",
        "description": "Access shell and bash command",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command given to run in shell",
                }
            },
            "required": ["command"],
        },
    }
]

def bash(command):
    log.debug("Called bash")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if not result: 
        return f"Error: unknown command '{command}'."
    return result 

TOOL_FUNCTIONS = {"bash": bash}

DENY = {"sudo", "su", "chmod", "chown", "kill", "crontab", "dd", "diskutil", "mkfs"}

SAFE = {"ls", "pwd", "cat", "head", "tail", "wc", "echo", "file", "stat",
        "which", "whoami", "date", "uname", "grep", "rg", "find", "git"}

# 有条件安全：命令本身 OK，但带了这些参数就不算安全
UNSAFE_FLAGS = {
    "find": {"-delete", "-exec", "-execdir", "-ok", "-okdir"},
}
SAFE_GIT_SUBCOMMANDS = {"status", "log", "diff", "branch", "show"}
SHELL_METACHARS = "/[;&|`$<>\n\r]/"


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
        return "deny", f"'{program}' is never allowed"

    # 4. 不在白名单里：问你
    if program not in SAFE:
        return "ask", f"'{program}' is not in the safe list"

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



while(True):
    # log.debug("started first while loop")
    user_input_string = input("Text for next step > ").strip()
    if user_input_string == "exit": 
            break
    if not user_input_string: continue 
    user_input = {"role": "user", "content": user_input_string}
    messages = messages + [user_input]
    response = None 

    while(True):
        # log.debug("started second while loop")
        response = CLIENT.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            tools=tools,
            tool_choice=tool_choice,
            messages=messages,
        )
        # log.debug(f"Initial response = {response}")
        tool_choice = {"type": "auto"}

        messages.append({"role": "assistant", "content":response.content}) 
        
        if response.stop_reason != "tool_use":
            log.debug(f"Response Stop reason = {response.stop_reason}, stopped responding")
            break
        else:
            # log.debug(f"Tool requested!")
            tool_results=[]
            for block in response.content:
                if block.type=="tool_use":
                    # log.debug(f"Calling tool{block.name}({block.input})")
                    command = block.input["command"]
                    decision, reason = check_command(command)

                    if decision == "allow":
                        log.debug(f"Auto-approved: {command}")
                        output = bash(command)
                    elif decision == "deny":
                        output = f"Blocked: {reason}. The command was not run."
                    else:
                        print(f"\nClaude wants to run: {command}")
                        print(f"Reason for asking: {reason}")
                        if input("Approve? (y/n) > ").strip().lower() == "y":
                            output = bash(command)
                        else:
                            output = "The user rejected this command. It was not run."

                    # log.debug(f"Got output {str(output)})")
                    tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(output),
                        })
                    # log.debug(f"Tool results appended {tool_results})")
            messages.append({"role":"user", "content":tool_results})  

    for block in response.content:
        if block.type == "text":
            print("Claude", block.text)
