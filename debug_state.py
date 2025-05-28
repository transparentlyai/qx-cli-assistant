#!/usr/bin/env python3

from src.qx.core.markdown_buffer import MarkdownStreamBuffer

def test_state_tracking():
    print('=== Testing state tracking ===')
    
    buffer = MarkdownStreamBuffer(max_buffer_size=100)
    
    # Test the state tracking
    chunks = ['```python\n', 'code line 1\n', 'code line 2\n', '```\n']
    
    for i, chunk in enumerate(chunks):
        print(f'\nChunk {i+1}: {repr(chunk)}')
        print(f'  Before: _in_code_block={buffer._in_code_block}, buffer={repr(buffer.buffer)}')
        
        result = buffer.add_content(chunk)
        
        print(f'  After: _in_code_block={buffer._in_code_block}, buffer={repr(buffer.buffer)}')
        print(f'  Rendered: {result is not None}')
        if result:
            print(f'  Content: {repr(result)}')

if __name__ == '__main__':
    test_state_tracking()