from utils.core import *
import subprocess
import shlex
import time

#让程序在意外情况下不要崩溃
try:
    import readline
    # #143 UTF-8 backspace fix for macOS libedit
    readline.parse_and_bind('set bind-tty-special-chars off')
    readline.parse_and_bind('set input-meta on')
    readline.parse_and_bind('set output-meta on')
    readline.parse_and_bind('set convert-meta off')
except ImportError:
    pass

log = get_logger(__name__)
log.debug("starting")

tool_choice = {"type": "auto"}

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
    


TOOL_FUNCTIONS = {"bash": bash}

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



def agent_loop(messages: list, tool_choice = {"type": "auto"}): 
    while(True):
        # log.debug("started second while loop")
        response = CLIENT.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            tools=tools,
            tool_choice=tool_choice,
            messages=messages,
            system=SYSTEM_PROMPT,
        )
        # log.debug(f"Initial response = {response}")
        tool_choice = {"type": "auto"}

        messages.append({"role": "assistant", "content":response.content}) 
        
        if response.stop_reason != "tool_use":
            # log.debug(f"Response Stop reason = {response.stop_reason}, stopped responding")
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
                        # log.debug(f"Auto-approved: {command}")
                        console.print("[bold #859900]✓ approved[/]")
                        output = bash(command)
                    elif decision == "deny":
                        console.print(f"[bold red]x Denied[/] {escape(command)}") 
                        console.print(f"  [dim]{escape(reason)}[/]")
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
    return response  

    

# -- Entry point --
if __name__ == "__main__":
    messages = []
    while(True):
        try:
            # \001/\002 tell Readline the ANSI escapes have zero display width.
            query = input("\001\033[36m\002toy-harness >> \001\033[0m\002")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break

        # log.debug("started first while loop")
        query = {"role": "user", "content": query}
        messages.append(query)
        response = agent_loop(messages,tool_choice=tool_choice)

        for block in response.content:
                    if block.type == "text":
                        console.print(Markdown(block.text, code_theme="solarized-light"))
