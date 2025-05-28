#!/usr/bin/env python3

from src.qx.core.markdown_buffer import MarkdownStreamBuffer

def test_problematic_scenarios():
    print('=== Testing problematic scenarios ===')
    
    # Test 1: Large non-code content that forces renders
    print('\n--- Test 1: Large non-code content ---')
    buffer = MarkdownStreamBuffer(max_buffer_size=100)
    
    # Add a long list that should trigger emergency renders
    list_items = [f"- Item {i} with some longer text to make it bigger\n" for i in range(10)]
    
    for i, item in enumerate(list_items):
        result = buffer.add_content(item)
        if result or i % 3 == 0:
            print(f'Item {i}: rendered={result is not None}, buffer_size={len(buffer.buffer)}')
            if result:
                print(f'  Rendered: {repr(result[:50])}...')
    
    # Now add a code block after the list
    result = buffer.add_content('\n```python\n')
    print(f'Code start: rendered={result is not None}, in_code_block={buffer._in_code_block}')
    
    result = buffer.add_content('def test(): pass\n')
    print(f'Code content: rendered={result is not None}, in_code_block={buffer._in_code_block}')
    
    result = buffer.add_content('```\n')
    print(f'Code end: rendered={result is not None}, in_code_block={buffer._in_code_block}')
    if result:
        print(f'  Final code render: {repr(result)}')
    
    final = buffer.flush()
    if final:
        print(f'Final flush: {repr(final)}')

def test_sentence_endings():
    print('\n=== Testing sentence endings in lists ===')
    
    buffer = MarkdownStreamBuffer(max_buffer_size=300)
    
    # This might trigger sentence-ending renders mid-list
    chunks = [
        "- First item ends here.\n",  # This might trigger render due to ".\n"
        "- Second item continues.\n",
        "- Third item.\n",
        "```python\n",
        "code here\n",
        "```\n"
    ]
    
    renders = []
    for i, chunk in enumerate(chunks):
        result = buffer.add_content(chunk)
        print(f'Chunk {i}: {repr(chunk)} -> rendered={result is not None}')
        if result:
            renders.append(result)
            print(f'  Content: {repr(result)}')
    
    final = buffer.flush()
    if final:
        renders.append(final)
    
    # Check if code block got split
    full_content = ''.join(renders)
    code_blocks = full_content.count('```')
    print(f'Total ``` count: {code_blocks}')
    if code_blocks % 2 != 0:
        print('⚠️  Odd number of ``` - code block broken!')

if __name__ == '__main__':
    test_problematic_scenarios()
    test_sentence_endings()