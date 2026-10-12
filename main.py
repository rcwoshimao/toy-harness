import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

model="claude-haiku-5-5"
max_tokens=1024
messages=[]

while(True): 
    user_input = input("Text for next step > ").strip()
    if user_input == "exit": 
        break
    if not user_input: continue 
    messages.append({"role": "user", "content": user_input})
    result = anthropic.Anthropic().messages.create(
    model="claude-haiku-5-5",
    max_tokens=1024,
    messages=messages,
    )
    
    messages.append({"role": "assistant", "content": result.content})
    print(result)

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


