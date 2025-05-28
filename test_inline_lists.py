#!/usr/bin/env python3

from src.qx.core.markdown_buffer import MarkdownStreamBuffer

def test_inline_list_issue():
    print('=== Testing inline list display issue ===')
    
    buffer = MarkdownStreamBuffer(max_buffer_size=200)
    
    # Simulate a typical list streaming scenario
    chunks = [
        "Here's my list:\n\n",
        "- First item\n",
        "- Second item with more text\n",
        "- Third item\n",
        "\nSome text after the list\n\n",
        "- New list starting\n",
        "- Another item"
    ]
    
    renders = []
    print('Streaming chunks:')
    for i, chunk in enumerate(chunks):
        print(f'\nChunk {i}: {repr(chunk)}')
        result = buffer.add_content(chunk)
        if result:
            renders.append(result)
            print(f'  RENDERED: {repr(result)}')
            # Check if this looks like broken list formatting
            if '- ' in result and not result.lstrip().startswith('- '):
                print('  ⚠️  WARNING: List item not at start of line!')
    
    final = buffer.flush()
    if final:
        renders.append(final)
        print(f'\nFinal flush: {repr(final)}')
    
    # Reconstruct full output
    full_output = ''.join(renders)
    print('\n=== Full output ===')
    print(full_output)
    
    # Check for inline list issues
    print('\n=== Analysis ===')
    lines = full_output.split('\n')
    for i, line in enumerate(lines):
        if '- ' in line and not line.lstrip().startswith('- '):
            print(f'Line {i+1} has inline list marker: {repr(line)}')

if __name__ == '__main__':
    test_inline_list_issue()