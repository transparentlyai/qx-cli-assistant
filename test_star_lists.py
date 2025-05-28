#!/usr/bin/env python3

from src.qx.core.markdown_buffer import MarkdownStreamBuffer

def test_star_lists():
    print('=== Testing star (*) lists ===')
    
    buffer = MarkdownStreamBuffer(max_buffer_size=200)
    
    # Test with * lists
    chunks = [
        "Here's my list:\n\n",
        "* First item\n",
        "* Second item with more text\n",
        "* Third item.\n",  # With period
        "\nSome text after the list\n\n",
        "* New list starting\n",
        "* Another item"
    ]
    
    renders = []
    print('Streaming chunks:')
    for i, chunk in enumerate(chunks):
        print(f'\nChunk {i}: {repr(chunk)}')
        result = buffer.add_content(chunk)
        if result:
            renders.append(result)
            print(f'  RENDERED: {repr(result)}')
    
    final = buffer.flush()
    if final:
        renders.append(final)
        print(f'\nFinal flush: {repr(final)}')
    
    # Reconstruct full output
    full_output = ''.join(renders)
    print('\n=== Full output ===')
    print(full_output)
    
    # Test what _is_in_list_context thinks about * lists
    print('\n=== Testing list context detection ===')
    test_buffers = [
        "* Item 1\n",
        "* Item 1\n* Item 2\n",
        "* Item with period.\n"
    ]
    
    for test_buf in test_buffers:
        buffer.buffer = test_buf
        in_context = buffer._is_in_list_context()
        print(f'Buffer: {repr(test_buf)} -> in_list_context: {in_context}')

if __name__ == '__main__':
    test_star_lists()