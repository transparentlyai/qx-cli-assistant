#!/usr/bin/env python3

from src.qx.core.markdown_buffer import MarkdownStreamBuffer

def debug_parser():
    print('=== Debugging markdown parser detection ===')
    
    buffer = MarkdownStreamBuffer(max_buffer_size=300)
    
    # Test what the parser sees for list items
    test_buffers = [
        "- First item ends here.\n",
        "- First item ends here.\n- Second item",
        "- Item 1\n- Item 2\n- Item 3.\n"
    ]
    
    for i, test_buffer in enumerate(test_buffers):
        print(f'\nTest {i+1}: {repr(test_buffer)}')
        buffer.buffer = test_buffer
        
        # Check what _is_inside_markdown_construct thinks
        is_inside = buffer._is_inside_markdown_construct()
        print(f'  _is_inside_markdown_construct: {is_inside}')
        
        # Check sentence ending detection
        sentence_end = (
            test_buffer.endswith(".\n") or 
            test_buffer.endswith("!\n") or 
            test_buffer.endswith("?\n") or 
            test_buffer.endswith(":\n")
        )
        print(f'  Sentence ending: {sentence_end}')
        
        # Parse tokens to see what markdown-it detects
        try:
            tokens = buffer.md_parser.parse(test_buffer)
            print(f'  Tokens: {len(tokens)}')
            for token in tokens:
                if token.type in ['list_item_open', 'list_item_close', 'bullet_list_open', 'bullet_list_close']:
                    print(f'    {token.type} (nesting: {token.nesting})')
            
            nesting_level = sum(token.nesting for token in tokens)
            print(f'  Net nesting level: {nesting_level}')
        except Exception as e:
            print(f'  Parse error: {e}')

if __name__ == '__main__':
    debug_parser()