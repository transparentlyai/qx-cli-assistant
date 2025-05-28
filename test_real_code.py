#!/usr/bin/env python3

from src.qx.core.markdown_buffer import MarkdownStreamBuffer
from pathlib import Path

def test_with_real_code():
    print('=== Testing with real llm.py content ===')
    
    # Read the actual llm.py file
    llm_path = Path('/home/mauro/projects/qx/src/qx/core/llm.py')
    content = llm_path.read_text()
    
    # Simulate streaming the file as a code block
    buffer = MarkdownStreamBuffer(max_buffer_size=500)  # Smaller buffer to trigger issues
    
    # Start code block
    result = buffer.add_content('```python\n')
    print(f'Opening: rendered={result is not None}, buffer_size={len(buffer.buffer)}')
    
    # Stream the file content in chunks
    chunk_size = 100
    renders = []
    
    for i in range(0, len(content), chunk_size):
        chunk = content[i:i+chunk_size]
        result = buffer.add_content(chunk)
        
        if result or len(buffer.buffer) % 200 == 0:  # Log every 200 chars or render
            in_fenced = buffer._is_in_open_fenced_code_block()
            print(f'Chunk {i//chunk_size}: rendered={result is not None}, buffer_size={len(buffer.buffer)}, in_fenced={in_fenced}')
            
            if result:
                renders.append(result)
                print(f'  RENDERED {len(result)} chars')
                # Check if render broke the code block
                if not result.startswith('```') and '```' in result:
                    print(f'  ⚠️  BROKEN CODE BLOCK: starts with {repr(result[:50])}')
    
    # Close the code block
    result = buffer.add_content('\n```\n')
    if result:
        renders.append(result)
    print(f'Closing: rendered={result is not None}, buffer_size={len(buffer.buffer)}')
    
    # Flush any remaining
    final = buffer.flush()
    if final:
        renders.append(final)
        print(f'Final flush: {len(final)} chars')
    
    print(f'\nTotal renders: {len(renders)}')
    for i, render in enumerate(renders):
        starts_with_backticks = render.startswith('```')
        ends_with_backticks = render.rstrip().endswith('```')
        print(f'Render {i+1}: {len(render)} chars, starts_with_```={starts_with_backticks}, ends_with_```={ends_with_backticks}')
        if not starts_with_backticks and i == 0:
            print(f'  ⚠️  First render should start with ```')
        if render.count('```') % 2 == 1 and not ends_with_backticks:
            print(f'  ⚠️  Odd number of ``` but doesn\'t end with them')

if __name__ == '__main__':
    test_with_real_code()