#!/usr/bin/env python3

from src.qx.core.markdown_buffer import MarkdownStreamBuffer

def test_specific_inline_issue():
    print('=== Testing specific inline list scenarios ===')
    
    # Scenario 1: Very short buffer causing frequent renders
    print('\n--- Scenario 1: Small buffer with * lists ---')
    buffer = MarkdownStreamBuffer(max_buffer_size=30)  # Very small
    
    chunks = [
        "List:\n",
        "* Item one\n",
        "* Item two\n",
        "* Item three\n"
    ]
    
    renders = []
    for chunk in chunks:
        result = buffer.add_content(chunk)
        print(f'Add: {repr(chunk)}')
        if result:
            renders.append(result)
            print(f'  => {repr(result)}')
    
    final = buffer.flush()
    if final:
        renders.append(final)
    
    print('\nJoined output:')
    print(''.join(renders))
    
    # Scenario 2: Mixed content that might confuse renderer
    print('\n--- Scenario 2: Mixed paragraph and list ---')
    buffer = MarkdownStreamBuffer(max_buffer_size=100)
    
    chunks = [
        "Some text * with asterisk\n",
        "* Real list item\n",
        "More text\n",
        "* Another list\n"
    ]
    
    for chunk in chunks:
        result = buffer.add_content(chunk)
        print(f'Add: {repr(chunk)}')
        if result:
            print(f'  => {repr(result)}')
    
    print(f'Flush: {repr(buffer.flush())}')

if __name__ == '__main__':
    test_specific_inline_issue()