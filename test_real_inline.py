#!/usr/bin/env python3

from src.qx.core.markdown_buffer import MarkdownStreamBuffer

def test_buffer_edge_cases():
    print('=== Testing buffer edge cases that might cause inline lists ===')
    
    # Test 1: Buffer cuts in middle of list
    print('\n--- Test 1: Buffer size forces mid-list render ---')
    buffer = MarkdownStreamBuffer(max_buffer_size=50)
    
    chunks = [
        "Some intro text here\n",
        "- First list item",  # No newline
        " continues here\n",
        "- Second item\n"
    ]
    
    for chunk in chunks:
        result = buffer.add_content(chunk)
        print(f'Add: {repr(chunk)}')
        if result:
            print(f'  => {repr(result)}')
    
    print(f'Flush: {repr(buffer.flush())}')
    
    # Test 2: Paragraph merging with lists
    print('\n--- Test 2: Paragraph and list interaction ---')
    buffer = MarkdownStreamBuffer(max_buffer_size=100)
    
    chunks = [
        "This is a paragraph",
        " - not a list item\n",  # This might be misinterpreted
        "- But this is a list\n"
    ]
    
    for chunk in chunks:
        result = buffer.add_content(chunk)
        print(f'Add: {repr(chunk)}')
        if result:
            print(f'  => {repr(result)}')
    
    print(f'Flush: {repr(buffer.flush())}')

if __name__ == '__main__':
    test_buffer_edge_cases()