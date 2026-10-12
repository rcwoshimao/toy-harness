import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

# ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

message = anthropic.Anthropic().messages.create(
    model="claude-haiku-5-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello, Claude"}],
)
print(message)


"""
(toy-harness) rebeccachen@MacBookPro toy-harness % python main.py
Message(id='msg_011CfwQGSrBBp721YoxZP116',
 container=None, 
 content=[TextBlock(citations=None, text='Hello! How can I help you today?', type='text')], 
 diagnostics=None, 
 model='claude-haiku-5-5', 
 role='assistant', 
 stop_details=None, 
 stop_reason='end_turn', 
 stop_sequence=None, type='message', usage=Usage(cache_creation=CacheCreation(ephemeral_1h_input_tokens=0, ephemeral_5m_input_tokens=0), cache_creation_input_tokens=0, 
 cache_read_input_tokens=0, 
 inference_geo='global', 
 input_tokens=15, 
 output_tokens=13, 
 output_tokens_details=OutputTokensDetails(thinking_tokens=0), 
 server_tool_use=None, 
 service_tier='standard'))
"""