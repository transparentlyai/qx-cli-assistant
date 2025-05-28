#!/usr/bin/env python3

from src.qx.core.markdown_buffer import MarkdownStreamBuffer

def test_mixed_content():
    print('=== Testing mixed content (lists + code blocks) ===')
    
    buffer = MarkdownStreamBuffer(max_buffer_size=200)
    
    # Simulate streaming mixed content
    content_chunks = [
        "Here's a list:\n\n",
        "- First item\n",
        "- Second item with some details\n", 
        "- Third item\n\n",
        "And here's some code:\n\n",
        "```python\n",
        "def example():\n",
        "    return 'hello'\n",
        "```\n\n",
        "- Another list item after code\n",
        "- Final item\n\n",
        "More text here."
    ]
    
    renders = []
    for i, chunk in enumerate(content_chunks):
        print(f'\nChunk {i+1}: {repr(chunk)}')
        print(f'  Before: _in_code_block={buffer._in_code_block}, buffer_size={len(buffer.buffer)}')
        
        result = buffer.add_content(chunk)
        
        print(f'  After: _in_code_block={buffer._in_code_block}, buffer_size={len(buffer.buffer)}')
        if result:
            renders.append(result)
            print(f'  RENDERED: {len(result)} chars')
            print(f'  Content preview: {repr(result[:100])}...')
    
    # Flush remaining
    final = buffer.flush()
    if final:
        renders.append(final)
        print(f'\nFinal flush: {len(final)} chars')
    
    print(f'\n=== Final Analysis ===')
    print(f'Total renders: {len(renders)}')
    
    # Check for problematic patterns
    full_content = ''.join(renders)
    print(f'Full content length: {len(full_content)}')
    
    # Look for code blocks that start mid-content
    lines = full_content.split('\n')
    for i, line in enumerate(lines):
        if '```' in line and not line.strip().startswith('```'):
            print(f'⚠️  Line {i+1}: Code block marker not at line start: {repr(line)}')

if __name__ == '__main__':
    test_mixed_content()