from utils.core import *
import subprocess

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
            log.debug(f"Tool requested!")
            tool_results=[]
            for block in response.content:
                if block.type=="tool_use":
                    log.debug(f"Calling tool{block.name}({block.input})")
                    command = block.input["command"]

                    print(f"\nClaude wants to run: {command}")
                    approved = input("Approve? (y/n) > ").strip().lower() == "y"

                    if approved:
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

    for block in response.content:
        if block.type == "text":
            print("Claude", block.text)
