#!/usr/bin/env python3

from src.qx.core.markdown_buffer import MarkdownStreamBuffer

def debug_buffer_size():
    print('=== Debugging buffer size issue ===')
    
    buffer = MarkdownStreamBuffer(max_buffer_size=100)
    
    # Test why individual list items are rendered
    item = "- Item 0 with some longer text to make it bigger\n"
    print(f'Item length: {len(item)}')
    print(f'Buffer max size: {buffer.max_buffer_size}')
    
    result = buffer.add_content(item)
    print(f'Result: rendered={result is not None}')
    print(f'Buffer size after: {len(buffer.buffer)}')
    print(f'In code block: {buffer._in_code_block}')
    print(f'Is in list context: {buffer._is_in_list_context()}')
    print(f'Buffer > max_size: {len(buffer.buffer) > buffer.max_buffer_size}')

if __name__ == '__main__':
    debug_buffer_size()