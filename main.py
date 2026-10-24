from utils.core import *
from rich.markup import escape
from tools.bash import tools, check_command, TOOL_FUNCTIONS

#让程序在意外情况下不要崩溃console.print(f"[bold red]x Denied[/] {escape(str(block.input))}")
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
log.debug(f"STARTED. IN {os.getcwd()}")

def agent_loop(messages: list): 
    while(True):
        # log.debug("started second while loop")
        response = CLIENT.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            tools=tools,
            messages=messages,
            system=SYSTEM_PROMPT,
        )
        # log.debug(f"Initial response = {response}")

        messages.append({"role": "assistant", "content":response.content}) 
        
        if response.stop_reason != "tool_use":
            # log.debug(f"Response Stop reason = {response.stop_reason}, stopped responding")
            break
        else:
            # log.debug(f"Tool requested!")
            tool_results=[]
            for block in response.content:
                if block.type=="tool_use":
                    log.debug(f"Calling tool{block.name}")

                    if block.name == "bash":   # TODO: move check into the tool
                        decision, reason = check_command(block.input["command"])
                    else:
                        decision, reason = "allow", "no check for this tool yet"

                    if decision == "allow":
                        # log.debug(f"Auto-approved: {command}")
                        console.print("[bold #859900]✓ approved[/]")
                        output = TOOL_FUNCTIONS[block.name](**block.input)
                    elif decision == "deny":
                        console.print(f"[bold red]x Denied[/] {escape(str(block.input))}") 
                        console.print(f"  [dim]{escape(reason)}[/]")
                        output = f"Blocked: {reason}. The command was not run."
                    else:
                        print(f"\nClaude wants to run: {block.input}")
                        print(f"Reason for asking: {reason}")
                        if input("Approve? (y/n) > ").strip().lower() == "y":
                            output = TOOL_FUNCTIONS[block.name](**block.input)
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
    # This is the big loop that prints "toy-harness>>" prefix. We simply refractored the agent loop out, the agent loop being the inner while loop. it is nothing crazy. 
    while(True):
        try:
            # \001/\002 tell Readline the ANSI escapes have zero display width.
            query = input("\001\033[36m\002toy-harness >> \001\033[0m\002")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break

        query = {"role": "user", "content": query}

        messages.append(query)
        response = agent_loop(messages)
        for block in response.content:
                    if block.type == "text":
                        console.print(Markdown(block.text, code_theme="solarized-light"))
