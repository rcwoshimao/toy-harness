import anthropic
import os
import copy
from dotenv import load_dotenv

load_dotenv()

model="claude-haiku-5-5"
max_tokens=1024
messages=[]

while(True): 
    user_input_string = input("Text for next step > ").strip()
    if user_input_string == "exit": 
        break
    if not user_input_string: continue 
    user_input = {"role": "user", "content": user_input_string}
    temp_messages=messages + [user_input]

    try: 
        result = anthropic.Anthropic().messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=temp_messages,
        )
    except anthropic.APIError as e:
        print(e)
    else: 
        messages.append(user_input)
        messages.append({"role": "assistant", "content": result.content})
        print(result.content)
    # print(f"messages:\n {messages}")



# message = anthropic.Anthropic().messages.create(
#     model="claude-haiku-5-5",
#     max_tokens=1024,
#     messages=[{"role": "user", "content": "Hello, Claude"}],
# )

# message = anthropic.Anthropic().messages.create(
#     model="claude-opus-5-5",
#     max_tokens=1024,
#     messages=[
#         {"role": "user", "content": "Hello, Claude"},
#         {"role": "assistant", "content": "Hello!"},
#         {"role": "user", "content": "Can you describe LLMs to me?"},
#     ],
# )
# print(message)


