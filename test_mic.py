from mic.mic.core import process_input

print('--- Testing mic (Internal) ---')

# 1. Test conversational AI
print('\nTest 1: Conversational AI (hello)')
print(f'mic: {process_input("hello")}')
print('\nTest 2: Conversational AI (how are you)')
print(f'mic: {process_input("how are you")}')
print('\nTest 3: Conversational AI (what can you do)')
print(f'mic: {process_input("what can you do")}')

# 2. Test web search (simulated)
print('\nTest 4: Web Search (simulated)')
print(f'mic: {process_input("web search: latest AI news")}')

# 3. Test code generation
print('\nTest 5: Code Generation (hello world)')
print(f'mic: {process_input("generate code: hello world")}')
print('\nTest 6: Code Generation (simple web server in python)')
print(f'mic: {process_input("generate code: simple web server in python")}')

# 4. Test code explanation
print('\nTest 7: Code Explanation (hello world print)')
print(f'mic: {process_input("explain code: print(\"hello, world!\")")}')

# 5. Test image generation
print('\nTest 8: Image Generation (cat playing piano)')
print(f'mic: {process_input("generate image: cat playing piano")}')

# 6. Test image analysis
print('\nTest 9: Image Analysis (cat.jpg)')
print(f'mic: {process_input("analyze image: cat.jpg")}')

# 7. Test creative writing (poem)
print('\nTest 10: Creative Writing (poem about nature)')
print(f'mic: {process_input("write poem about: nature")}')

# 8. Test creative writing (story)
print('\nTest 11: Creative Writing (story fantasy with characters dragon and knight)')
print(f'mic: {process_input("write story fantasy with characters dragon and knight")}')

# 9. Test data analysis
print('\nTest 12: Data Analysis (sales figures for Q1)')
print(f'mic: {process_input("analyze data: sales figures for Q1")}')

# 10. Test specialized domain insight
print('\nTest 13: Specialized Domain Insight (finance for stock market trends)')
print(f'mic: {process_input("get insight from finance for stock market trends")}')

# 11. Test unknown command
print('\nTest 14: Unknown Command')
print(f'mic: {process_input("what is the meaning of life")}')