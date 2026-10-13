from utils.core import *

log = get_logger(__name__)
log.debug("starting")

tool_choice = {"type": "tool", "name": "calculator"}

tools=[
    {
        "name": "calculator",
        "description": "a calculator that only allows two operations: calculating 1 + 1 and 1 - 1.",
        "input_schema":{
            "type": "object", 
            "properties": {
                "action": {  
                    "type":"string",
                    "enum":["1+1","1-1"],
                    "description":"which operation to perform.",
                },
            },
            "required": ["action"],
        },
    },
]

def calculate(action, **kwargs):
    log.debug("Called calculate")
    if action=="1+1":
        return 3
    if action=="1-1":
        return 0
    return f"Error: unknown action '{action}'."

TOOL_FUNCTIONS = {"calculator": calculate}


while(True):
    log.debug("started first while loop")
    user_input_string = input("Text for next step > ").strip()
    if user_input_string == "exit": 
            break
    if not user_input_string: continue 
    user_input = {"role": "user", "content": user_input_string}
    messages = messages + [user_input]
    response = None 

    while(True):
        log.debug("started second while loop")
        response = CLIENT.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            tools=tools,
            tool_choice=tool_choice,
            messages=messages,
        )
        log.debug(f"Initial response = {response}")
        tool_choice = {"type": "auto"}

        messages.append({"role": "assistant", "content":response.content}) 
        
        if response.stop_reason != "tool_use":
            log.debug(f"Response Stop reason = {response.stop_reason}, stopped responding")
            break
        else:
            log.debug(f"Response stopped, Tools requested. ")
            tool_results=[]
            for block in response.content:
                if block.type=="tool_use":
                    log.debug(f"Calling tool{block.name}({block.input})")
                    output = TOOL_FUNCTIONS[block.name](**block.input)

                    log.debug(f"Got output {str(output)})")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(output),
                    })
                    log.debug(f"Tool results appended {tool_results})")
            messages.append({"role":"user", "content":tool_results})  

    for block in response.content:
        if block.type == "text":
            print("Claude", block.text)

    # print(messages)

             


    
raise SystemExit

tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a given location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and state, e.g. San Francisco, CA",
                }
            },
            "required": ["location"],
        },
    }
]
messages = [{"role": "user", "content": "What's the weather in San Francisco?"}]

# Claude replies with a tool_use block naming the tool and its arguments.
response = CLIENT.messages.create(
    model=MODEL,
    max_tokens=MAX_TOKENS,
    tools=tools,
    # Ask for at most one tool call per turn.
    tool_choice={"type": "auto", "disable_parallel_tool_use": True},
    messages=messages,
)
tool_use = next(block for block in response.content if block.type == "tool_use")
print(f"Claude called {tool_use.name} with {json.dumps(tool_use.input)}")

# Run the tool, then send the result back in a tool_result block.
weather = 'json.dumps({"temp_f": 67, "conditions": "foggy", "wind_mph": 12})"' # your weather lookup goes here
messages += [
    {"role": "assistant", "content": response.content},
    {
        "role": "user",
        "content": [
            {"type": "tool_result", "tool_use_id": tool_use.id, "content": weather}
        ],
    },
]

followup = CLIENT.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "auto", "disable_parallel_tool_use": True},
    messages=messages,
)

# Claude uses the result to answer the original question.
final_text = next(block for block in followup.content if block.type == "text")
print(final_text.text)








response = CLIENT.messages.create(
    model=model,
    max_tokens=max_tokens,
    tools=[{"type": "web_search_20260209", "name": "web_search"}],
    messages=[{"role": "user", "content": "I need a latest wholesome news."}],
)
print(response.content)





