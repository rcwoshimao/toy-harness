```
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
```

```
(toy-harness) rebeccachen@MacBookPro toy-harness % python main.py                
Message(id='msg_011CfwRg9pXYfSv2TqRvKjFW', container=None, content=[ThinkingBlock(signature='CAQSuwUKEAgSGAI4AUIIdGhpbmtpbmcSDAKKl66btvXcjntE3RoMEhu7UQMHAFI6mRBcIjBxe0Y72yCcwiW3HU4amO/Ju1TP9QsRKgAYmTL9zbCFEItctL1b0AnvMan6TDMnMbIq2AQ5LnTN5kerPhtGHmggh71APbQnbqhqFPbrIryOcrqo/AV2AhS7JYcQd7QAs5s0OlEmB1LuK/qeRhgILSHMzPW86fp7RMveGdoDFfw95UkdjafObDyenst6S5dPqrXcFx3MkJek5LyoX2JA7NehMGv0UPKIOTCvzkkeQW642QWvXWZ5Q9aV7oba0Kn0C6Yqn/dK9zG+/Y1P6tjHzX8uMTedGIQ7T4+6JcdTiiGFaiLRxJUIrk3nNswMGH48y3cLCIMyM75IG460kIE5q1uTKqHoTuX61+Pk7hbvBpd0BPE/7Kh03khbixcmqLGLwbJ8v4lmpDee9QUj8byXuQdRkTYbLDr7eTBunTBE+5XfU2/OgVDrpx+vAy1VMt9B0VbXsK2E6NstGnd4QFY+upThWGbKEn1VSKOeyLAkeq+axHzKsYvEgswNg27IS96uJVVaQ5XoQ7DMgkc0LauZQ0Cwkn4va1bPN0ASfAQ3vojTp8nLahzZdyUAlLmswaeNbnBX9SkSKmQC3N3CYAYBUUqwlxPv/xttjL+07QLj3W91c9/wucQ6yJUmEhdsqSvRQcUlt5r5yiOOc54v0G/ovAbH4mFJbNiy6uxblF3kFSqBK2x+i7Hj5PpgSzvzU7kyd2pgBmHYGI6AhSMahlrxSP9eqYSkYXeb77iaFY9VSLgBfSadFq3iyTtVtrqlG6+8B3hk3IPVnGiIYISrXfAWenm0xHvpDg2lF9wQbZo14bvJ0suPl0GgLPovzeCY1/SYypgFgvEbjJZkzKyRt0BwELbIct0w0Yh7RnDwbgkYAQ==', 
thinking='', 
type='thinking'), 
TextBlock(citations=None, 
text='LLMs (Large Language Models) are AI systems trained to understand and generate human language. I\'m one myself, so this is a bit of a self-description!\n\n## The Basic Idea\n\nAt its core, an LLM is trained to **predict the next word** (technically, the next "token," which can be a word or part of a word) given the text that came before it. That sounds simple, but doing it well across billions of examples forces the model to pick up grammar, facts, reasoning patterns, writing styles, and more.\n\n## How They\'re Built\n\n1. **Architecture:** Most modern LLMs use the **Transformer** architecture (introduced in 2017). Its key innovation, called *attention*, lets the model weigh how relevant each word in a passage is toevery other word, which helps it track context over long stretches of text.\n\n2. **Pre-training:** The model is trained on enormous amounts of text from books, websites, code, and other sources. During this phase it adjusts billions of internal numbers (called *parameters*) to get better at predicting text.\n\n3. **Fine-tuning:** The raw model is then refined tobe more helpful, accurate, and safe, often with techniques like *reinforcement learning from human feedback* (RLHF), where people rate responses and the model learns from those preferences.\n\n## What They Can Do\n\n- Answer questions and explain concepts\n- Write and edit essays, emails, stories, and code\n- Summarize and translate text\n- Brainstorm ideas and help with analysis\n\n## Key Limitations\n\n- **Hallucinations:** They can state false information confidently.\n- **Knowledge cutoffs:** Their knowledge comes from training data up to a certain date.\n- **No true understanding (debated):** Theywork by learning statistical patterns, and whether that amounts to "understanding" is an open philosophical question.\n- **Bias:** They can reflect biases present in their training data.\n\n## Examples\n\nWell-known LLMs include Claude (made by Anthropic), GPT models (OpenAI), Gemini (Google), and Llama (Meta).\n\nWould you like me to go deeper on any part, such as how attention works or how training happens?', type='text')], 
diagnostics=None, 
model='claude-opus-5-5', 
role='assistant', 
stop_details=None, 
stop_reason='end_turn', 
stop_sequence=None, 
type='message', 
usage=Usage(cache_creation=CacheCreation(ephemeral_1h_input_tokens=0, ephemeral_5m_input_tokens=0), cache_creation_input_tokens=0, 
cache_read_input_tokens=0, 
inference_geo='global', 
input_tokens=35, 
output_tokens=722, 
output_tokens_details=OutputTokensDetails(thinking_tokens=44), 
server_tool_use=None, 
service_tier='standard'))
```