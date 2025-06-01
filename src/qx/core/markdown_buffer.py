import asyncio
import re
import threading
from typing import Optional

from markdown_it import MarkdownIt
from markdown_it.token import Token  # For type hinting


class MarkdownStreamBuffer:
    """
    A buffer that accumulates streaming content and determines safe points to render
    Markdown without breaking formatting, using markdown-it-py for better semantic understanding.
    """

    def __init__(
        self, max_buffer_size: int = 65000,
        max_list_buffer_size: int = 8000
    ):  # Increased default max_buffer_size
        self.buffer: str = ""
        self.max_buffer_size: int = max_buffer_size
        self.max_list_buffer_size: int = max_list_buffer_size  # Separate limit for lists
        self.md_parser: MarkdownIt = MarkdownIt()
        self._has_rendered_once: bool = False  # Track if we've rendered anything yet
        # Common Markdown block-level elements that have distinct open/close tokens
        # and affect nesting levels directly.
        self._nesting_block_tokens = {
            "blockquote_open",
            "bullet_list_open",
            "ordered_list_open",
            "list_item_open",
            # "paragraph_open" is tricky as almost everything is wrapped in it.
            # We rely on its corresponding _close for balancing.
        }
        # Common inline elements
        self._nesting_inline_tokens = {
            "em_open",
            "strong_open",
            "link_open",
            "image_open",
            # Note: `code_inline` has nesting 0. `backtick_open` isn't a standard token type.
        }
        # Thread safety lock
        self._lock = threading.Lock()

    def add_content(self, content: str) -> Optional[str]:
        """
        Add content to the buffer and return content to render if safe, otherwise None.
        Thread-safe version.

        Returns:
            str: Content to render now, or None if should wait for more content.
        """
        if not content:  # Guard against empty content
            return None
        
        with self._lock:
            self.buffer += content

            if self._should_render():
                content_to_render = self.buffer  # Capture the buffer content
                self.buffer = ""                  # Always clear the buffer
                self._has_rendered_once = True    # Always mark as rendered attempt
                
                # Always return the content unit identified by _should_render.
                # The downstream Markdown renderer will handle its significance.
                return content_to_render

            return None

    def flush(self) -> str:
        """
        Flush any remaining buffer content (called when stream ends).
        Thread-safe version.

        Returns:
            str: Any remaining buffer content.
        """
        with self._lock:
            content_to_render = self.buffer
            self.buffer = ""
            return content_to_render


    def _is_in_open_fenced_code_block(self) -> bool:
        """Checks if the buffer is currently inside an open fenced code block."""
        return self.buffer.count("```") % 2 == 1

    def _should_render(self) -> bool:
        """
        Determine if the current buffer should be rendered.
        """
        if not self.buffer:
            return False

        # 1. Check if we're in a list context with its own threshold
        if self._is_in_list_context() and len(self.buffer) > self.max_list_buffer_size:
            # For lists, use the smaller threshold to ensure more frequent rendering
            # But still check if we're at a safe breakpoint (end of line)
            if self.buffer.endswith('\n'):
                return True
            # If not at line end but way over limit, force render
            elif len(self.buffer) > self.max_list_buffer_size * 1.5:
                return True
        
        # 2. Emergency fallback: render if buffer gets too large, but respect markdown boundaries
        if len(self.buffer) > self.max_buffer_size:
            # If we're inside a fenced code block, NEVER force render
            if self._is_in_open_fenced_code_block():
                return False
            else:
                # Not in code block, safe to render
                # print(f"DEBUG: Rendering due to max_buffer_size ({len(self.buffer)} > {self.max_buffer_size})")
                return True

        # 3. If inside an open fenced code block, do not render.
        if self._is_in_open_fenced_code_block():
            # print("DEBUG: Not rendering, inside open fenced code block.")
            return False

        # 4. If a fenced code block just cleanly closed (and we're not in another one)
        #    A block is cleanly closed if ``` is at the end, possibly with whitespace.
        if (
            self.buffer.count("```") > 0 and self.buffer.count("```") % 2 == 0
        ):  # Even number of fences means all are closed
            if self.buffer.rstrip().endswith(
                "```"
            ):  # Ends with ``` after stripping trailing whitespace
                # print("DEBUG: Rendering, fenced code block cleanly closed.")
                return True

        # 5. Paragraph breaks (double newline) are generally safe if not in other constructs.
        #    The _is_inside_markdown_construct will do a deeper check.
        #    If a double newline exists, and we are NOT inside a construct, it's a strong signal to render.
        #    Ensure buffer ends with \n\n or contains \n\n and then only whitespace
        normalized_buffer_for_nnd_check = (
            self.buffer.rstrip("\n") + "\n"
        )  # Ensures single trailing \n for consistent check
        if "\n\n" in normalized_buffer_for_nnd_check:
            # Check if the content after the last \n\n is only whitespace before deciding to render
            last_nnd_pos = self.buffer.rfind("\n\n")
            if last_nnd_pos != -1:
                content_after_nnd = self.buffer[last_nnd_pos + 2 :]
                if not content_after_nnd.strip():  # Only whitespace after the last \n\n
                    if not self._is_inside_markdown_construct(
                        check_lists_aggressively=False
                    ):
                        # print("DEBUG: Rendering, double newline and not inside construct.")
                        return True
                # If there's non-whitespace content after \n\n, check if it's a list starting
                elif re.match(r'^\s*[-*+]\s+', content_after_nnd.lstrip()):
                    # Don't render yet - new list is starting after paragraph break
                    return False
                # Let other rules decide for other content
            elif not self._is_inside_markdown_construct(
                check_lists_aggressively=False
            ):  # Buffer itself is just "\n\n" or similar
                # print("DEBUG: Rendering, double newline (buffer start) and not inside construct.")
                return True

        # 6. Check if we are inside any other Markdown construct. If so, don't render.
        if self._is_inside_markdown_construct():
            # print(f"DEBUG: Not rendering, _is_inside_markdown_construct returned True. Buffer: '{self.buffer}'")
            return False

        # 7. Basic safe break points (e.g., end of sentence followed by a newline)
        #    This is a weaker signal, apply if not inside constructs.
        #    BUT: Don't break on sentence endings if we're likely in a list context
        if (
            self.buffer.endswith(".\n")
            or self.buffer.endswith("!\n")
            or self.buffer.endswith("?\n")
            or self.buffer.endswith(":\n")
        ):
            # Check if we're in a list context - if so, don't render on sentence endings
            # This prevents breaking up lists into individual items
            if self._is_in_list_context():
                # print("DEBUG: Not rendering on sentence end - in list context.")
                return False
                
            # Additional safety check: ensure we have enough content to render meaningfully
            # This helps prevent rendering very short content that might be incomplete
            # BUT: Don't apply this check at the very beginning of the stream
            # to avoid buffering initial words unnecessarily
            stripped_buffer = self.buffer.strip()
            # Only apply minimum length check if we've already rendered something
            # (i.e., this isn't the first chunk of content)
            if hasattr(self, '_has_rendered_once') and self._has_rendered_once:
                if len(stripped_buffer) < 3:  # Very short content, might be incomplete
                    return False
                
            # print("DEBUG: Rendering, sentence end with newline.")
            return True

        # If buffer is moderately full and ends with a single newline,
        # and not inside a construct, consider rendering.
        # This helps with streaming line-by-line content that isn't part of a larger block.
        if len(self.buffer) > self.max_buffer_size / 4 and self.buffer.endswith("\n"):
            if (
                not self._is_inside_markdown_construct()
            ):  # Re-check, as state might have changed by earlier rules
                # print("DEBUG: Rendering, moderately full buffer ending with newline and not in construct.")
                return True

        # print(f"DEBUG: Not rendering, no specific condition met. Buffer: '{self.buffer}'")
        return False

    def _is_inside_markdown_construct(
        self, check_lists_aggressively: bool = True
    ) -> bool:
        """
        Check if we're currently inside any Markdown construct that shouldn't be broken,
        using markdown-it-py for more accuracy.
        `check_lists_aggressively` is for tuning list detection sensitivity.
        """
        current_buffer_stripped = self.buffer.strip()
        if not current_buffer_stripped:  # Ignore if buffer is empty or only whitespace
            return False

        # This check is primary in _should_render, but good for direct calls or safety.
        if self._is_in_open_fenced_code_block():
            # print("DEBUG_construct: Inside open fenced code block.")
            return True

        # Attempt to parse with markdown-it-py
        tokens: list[Token] = []
        try:
            # Parsing the raw buffer. `render()` is not needed here.
            tokens = self.md_parser.parse(self.buffer)
        except Exception as e:
            # If parsing fails (e.g., due to highly malformed Markdown mid-stream),
            # it's safer to assume we are in an unstable/incomplete state.
            # However, for very short content at the beginning, we might be too conservative
            if len(current_buffer_stripped) < 10:
                # For very short content, be less conservative about parsing failures
                # This prevents over-buffering short text at the beginning
                return False
            # print(f"DEBUG_construct: Parsing failed: {e}. Assuming inside construct.")
            return True

        # Check 1: Net nesting level from tokens
        # Positive nesting level indicates unclosed constructs (e.g., emphasis, list, blockquote).
        current_nesting_level = sum(token.nesting for token in tokens)
        if current_nesting_level > 0:
            # print(f"DEBUG_construct: Nesting level {current_nesting_level} > 0.")
            return True

        # Check 2: Unclosed inline code backticks (` `)
        # This is for cases where a single backtick is present and hasn't formed a code_inline token.
        # `code_inline` tokens have nesting 0.
        # We need to count backticks outside of fenced code blocks.
        text_outside_fences = ""
        parts = self.buffer.split("```")
        for i, part in enumerate(parts):
            if (
                i % 2 == 0
            ):  # Content outside or between (if nested, though not std) ``` blocks
                text_outside_fences += part
        if text_outside_fences.count("`") % 2 == 1:
            # print("DEBUG_construct: Unclosed inline code backtick.")
            return True

        # Check 3: Unterminated indented code block
        # An indented code block token (`code_block`) has nesting 0.
        # We check if the last significant block token was `code_block` and
        # the buffer doesn't clearly terminate it (e.g., with \n\n, which _should_render handles).
        if tokens:
            last_block_token: Optional[Token] = None
            # Iterate from the end to find the last "true" block token
            for token in reversed(tokens):
                if token.block and token.type not in {
                    "paragraph_open",
                    "paragraph_close",
                    "hr",
                    "heading_open",
                    "heading_close",
                }:
                    last_block_token = token
                    break

            if last_block_token and last_block_token.type == "code_block":
                # If the buffer ends with the content of this code block (or a superset, if streaming),
                # and isn't followed by a double newline (which would be a render signal).
                # The rstrip('\n') on content is because code_block content often includes a final \n.
                # Check if the buffer's end "looks like" it's continuing this code block.
                # This means it likely ends with the content of the code_block token or is a prefix of it.
                if self.buffer.rstrip("\n").endswith(
                    last_block_token.content.rstrip("\n")
                ) and not (self.buffer.rstrip("\n") + "\n").endswith("\n\n"):
                    # print("DEBUG_construct: Unterminated indented code block suspected.")
                    return True

        # Check 4: List item heuristic (especially for items without trailing newlines yet)
        if check_lists_aggressively and self._is_in_list_heuristic(tokens):
            # print("DEBUG_construct: List heuristic triggered.")
            return True

        # Check 5: Unclosed HTML tags (basic check)
        # This is a very simplified check. markdown-it-py handles HTML blocks/inline.
        # This is more for unterminated raw HTML that might be mid-stream.
        # Count open tags like <tag> or <tag attr=""> vs closing tags </tag>
        # Regex to find opening tags (excluding self-closing like <br/> or <img ... />)
        open_html_tags_matches = re.findall(
            r"<([a-zA-Z0-9]+)(?:\s[^>]*)?(?<!/)>", self.buffer
        )
        # Regex to find closing tags
        close_html_tags_matches = re.findall(r"</([a-zA-Z0-9]+)\s*>", self.buffer)

        # A more robust check would be to maintain a stack of open HTML tags.
        # For simplicity here, if there's an imbalance and the buffer ends with an unclosed tag start.
        if len(open_html_tags_matches) > len(close_html_tags_matches):
            # Check if the buffer ends with something like "<tag" or "<tag attr"
            last_lt = self.buffer.rfind("<")
            last_gt = self.buffer.rfind(">")
            if (
                last_lt != -1 and last_lt > last_gt
            ):  # Indicates an unclosed tag, e.g. "<div"
                # print("DEBUG_construct: Unclosed HTML tag suspected (ends with '<tag_start').")
                return True
            # Check if the last complete tag is an opening one without a corresponding closer immediately after (simplistic)
            # This is hard to do perfectly without full HTML parsing.
            # The markdown-it parser's html_block/html_inline tokens are better.
            # If the parser made an html_block and it's unclosed, nesting_level should catch it if it has nesting.
            # If it's raw HTML that markdown-it passes through as html_inline with nesting 0, this is a fallback.

        # print("DEBUG_construct: No specific construct detected as open.")
        return False

    def _is_in_list_heuristic(self, tokens: list[Token]) -> bool:
        """
        Heuristic to check if we are likely in the middle of typing a list item,
        especially one that doesn't have a newline yet.
        `tokens` are the tokens from parsing the current buffer.
        """
        if not self.buffer:
            return False

        # If markdown-it-py has an open list_item_open without a corresponding close,
        # current_nesting_level > 0 in _is_inside_markdown_construct should catch it.
        # This heuristic is for cases where the list item is too partial for a token to form,
        # or the last token was a paragraph inside a list item that isn't closed by \n\n yet.

        last_line = self.buffer.split("\n")[-1]
        # Use last_line (not stripped) to preserve leading space context for list item detection

        list_marker_pattern = (
            r"^\s*([-*+]|\d+\.)\s+"  # Marker followed by at least one space
        )
        # Simpler pattern for just the marker itself, potentially with no space after (yet)
        just_marker_pattern = r"^\s*([-*+]|\d+\.)$"

        if re.match(list_marker_pattern, last_line) or re.match(
            just_marker_pattern, last_line.rstrip()
        ):
            # If it matches the start of a list item:
            # Check if it's just the marker or marker + some text, and buffer doesn't end with \n\n
            # (if it ends with \n\n, _should_render would likely handle it if not inside another construct)
            if not (self.buffer.rstrip("\n") + "\n").endswith("\n\n"):
                # If current_nesting_level was already > 0 due to list_item_open, this is fine.
                # This is for cases like:
                #   - Buffer is "  - " (just marker, maybe waiting for text)
                #   - Buffer is "  - Item text" (no newline yet)
                return True
        return False

    def _is_in_list_context(self) -> bool:
        """
        Check if we're in a list context where we shouldn't break on sentence endings.
        This detects when the buffer contains list items and the last line looks like
        it could be part of a continuing list.
        """
        if not self.buffer:
            return False
        
        lines = self.buffer.split('\n')
        
        # Look for list markers in recent lines
        list_marker_pattern = r'^\s*([-*+]|\d+\.)\s+'
        
        # Check if any of the last few lines contain list markers
        lines_to_check = lines[-5:] if len(lines) >= 5 else lines  # Check more lines for nested lists
        has_list_markers = any(
            re.match(list_marker_pattern, line) 
            for line in lines_to_check if line.strip()
        )
        
        if not has_list_markers:
            return False
        
        # If we have list markers and the buffer doesn't end with double newline,
        # we're likely still in list context
        if not self.buffer.rstrip('\n').endswith('\n\n'):
            return True
        
        # Additional check: if the last non-empty line is indented (likely nested list continuation)
        # we're still in list context even after a single newline
        non_empty_lines = [line for line in lines if line.strip()]
        if non_empty_lines:
            last_line = non_empty_lines[-1]
            if last_line.startswith('  '):  # Indented, likely nested list
                return True
        
        return False


def create_markdown_buffer(max_size: int = 65000, max_list_size: int = 8000) -> MarkdownStreamBuffer:
    """
    Factory function to create a new MarkdownStreamBuffer.

    Args:
        max_size: Maximum buffer size before emergency flush. Default 65000 to handle large code blocks.
        max_list_size: Maximum buffer size for list content. Default 8000 for more responsive list rendering.

    Returns:
        MarkdownStreamBuffer: New buffer instance.
    """
    return MarkdownStreamBuffer(max_size, max_list_size)


if __name__ == "__main__":
    # Example Usage and Testing
    def process_stream(buffer: MarkdownStreamBuffer, chunks: list[str], test_name: str):
        print(f"\n--- Starting Stream: {test_name} ---")
        for i, chunk in enumerate(chunks):
            print(
                f"\n[+] Adding chunk {i + 1}: '{chunk}' (Buffer before: '{buffer.buffer}')"
            )
            render_output = buffer.add_content(chunk)
            if render_output:
                print(f"==> Rendered: '{render_output}'")
                print(f"--> Buffer after render: '{buffer.buffer}'")
            else:
                print(f"--> Buffered. Current buffer: '{buffer.buffer}'")

        final_output = buffer.flush()
        if final_output:
            print(f"\n[!] Flushing remaining: '{final_output}'")
        print(f"--- Stream Ended: {test_name} ---")

    # Test Case 1: Fenced Code Block
    b1 = create_markdown_buffer(max_size=50)
    stream1 = [
        "```python\n",
        "def hello():\n",
        "  print('hi')\n",
        "\n",
        "print('done')\n",
        "```\n",
        "Next para.",
    ]
    process_stream(b1, stream1, "Test Case 1: Fenced Code Block")

    # Test Case 2: Inline Code and Emphasis
    b2 = create_markdown_buffer(max_size=50)
    stream2 = [
        "This is `code",
        " and *italic*",
        " text.\nAnd **bold**",
        " too.\n\nNext.",
    ]
    process_stream(b2, stream2, "Test Case 2: Inline Code and Emphasis")

    # Test Case 3: Lists
    b3 = create_markdown_buffer(max_size=50)
    stream3 = ["- Item 1\n", "- Item 2 part", " A\n- Item 3\n\n", "Para after list."]
    process_stream(b3, stream3, "Test Case 3: Lists")

    # Test Case 4: List item without newline
    b4 = create_markdown_buffer(max_size=50)
    stream4 = ["- Item 1\n", "- Item 2 is being typed"]  # No newline after "typed"
    process_stream(b4, stream4, "Test Case 4: List item without newline")

    # Test Case 5: Max buffer size
    b5 = create_markdown_buffer(max_size=10)
    stream5 = ["abcdefghij", "klmnopqrstuvwxyz"]  # First chunk fills, second overflows
    process_stream(b5, stream5, "Test Case 5: Max buffer size")

    # Test Case 6: Paragraphs and sentence end
    b6 = create_markdown_buffer(max_size=100)
    stream6 = [
        "First sentence. ",
        "Second sentence.\n",
        "Third sentence starts.",
        "\n\nFourth sentence.",
    ]
    process_stream(b6, stream6, "Test Case 6: Paragraphs and sentence end")

    # Test Case 7: Indented code
    b7 = create_markdown_buffer(max_size=100)
    stream7 = [
        "Para:\n\n",
        "    def test():\n",
        "        pass\n",
        "    # comment\n",
        "\nNot code anymore.",
    ]
    process_stream(b7, stream7, "Test Case 7: Indented code")

    # Test Case 8: HTML tags (basic)
    b8 = create_markdown_buffer(max_size=100)
    stream8 = [
        "<div><span>Hello</span>",
        "</div>\n",
        "<p>Next",
        " paragraph</p>\n",
        "Final text.",
    ]
    process_stream(b8, stream8, "Test Case 8: HTML tags (basic)")

    # Test Case 9: Cleanly closed code block then more text
    b9 = create_markdown_buffer(max_size=100)
    stream9 = ["```\ncode\n```", "This is after code.\n\nAnd another para."]
    process_stream(b9, stream9, "Test Case 9: Cleanly closed code block then more text")

    # Test Case 10: Mixed constructs - List with bold/italic
    b10 = create_markdown_buffer(max_size=100)
    stream10 = [
        "- List item with *italic",
        " and **bold** ",
        "text*.\n",
        "- Next item `code`",
        "\n\nParagraph.",
    ]
    process_stream(
        b10, stream10, "Test Case 10: Mixed constructs - List with bold/italic"
    )

    # Test Case 11: Potentially problematic input (e.g., unusual characters, broken HTML)
    b11 = create_markdown_buffer(max_size=100)
    # This might cause markdown-it to struggle or produce unexpected tokens, testing the try-except.
    stream11 = [
        "Text with <unclosed ",
        "or b@dly formed <tag attr='val' \n",
        "Some normal text.\n\n",
    ]
    process_stream(b11, stream11, "Test Case 11: Problematic Input (Unclosed/Bad HTML)")

    # Test Case 12: Buffer ending with single newline, moderately full
    b12 = create_markdown_buffer(max_size=30)
    stream12 = [
        "This is a line of text that is getting longer.\n",
        "Another short line.\n",
    ]
    process_stream(b12, stream12, "Test Case 12: Moderately full, ends with newline")

    # Test Case 13: Double newline mid-buffer but with content after it
    b13 = create_markdown_buffer(max_size=100)
    stream13 = ["First part.\n\nSecond part starts", " immediately.\nThen a new line."]
    process_stream(b13, stream13, "Test Case 13: Double newline with content after")

    # Test Case 14: List item just marker
    b14 = create_markdown_buffer(max_size=50)
    stream14 = ["- Item 1\n", "- "]  # Just a list marker
    process_stream(b14, stream14, "Test Case 14: List item just marker")
