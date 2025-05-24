import logging
import httpx
from typing import Optional

from pydantic import BaseModel, Field
from rich.console import Console as RichConsole

from qx.core.user_prompts import request_confirmation

logger = logging.getLogger(__name__)

# Constants
MAX_CONTENT_LENGTH = 50000  # Max characters to return from a fetched page
REQUEST_TIMEOUT = 10  # seconds


class WebFetchPluginInput(BaseModel):
    """Input model for the WebFetchTool."""

    url: str = Field(..., description="The URL to fetch content from.")


class WebFetchPluginOutput(BaseModel):
    """Output model for the WebFetchTool."""

    url: str = Field(description="The URL that was attempted to be fetched.")
    content: Optional[str] = Field(
        None, description="The fetched content, or None if an error occurred."
    )
    error: Optional[str] = Field(
        None, description="Error message if the operation failed or was denied."
    )
    status_code: Optional[int] = Field(
        None, description="HTTP status code of the response, if available."
    )
    truncated: bool = Field(
        False, description="True if the content was truncated due to size limits."
    )


async def web_fetch_tool(
    console: RichConsole, args: WebFetchPluginInput
) -> WebFetchPluginOutput:
    """
    Tool to fetch content from a specified URL on the internet.
    Requires user confirmation for security reasons.
    """
    url_to_fetch = args.url.strip()

    if not url_to_fetch:
        err_msg = "Error: Empty URL provided."
        logger.error(err_msg)
        console.print(f"[error]{err_msg}[/error]")
        return WebFetchPluginOutput(
            url="", content=None, error=err_msg, status_code=None, truncated=False
        )

    prompt_msg = f"Allow QX to fetch content from URL: '{url_to_fetch}'?"
    decision_status, _ = await request_confirmation(
        prompt_message=prompt_msg,
        console=console,
        allow_modify=False,  # URL modification not allowed for this tool
    )

    if decision_status not in ["approved", "session_approved"]:
        error_message = (
            f"Web fetch operation for '{url_to_fetch}' was {decision_status} by user."
        )
        logger.warning(error_message)
        if decision_status == "denied":
            console.print(
                f"[warning]Web fetch denied by user:[/warning] {url_to_fetch}"
            )
        elif decision_status == "cancelled":
            console.print(
                f"[warning]Web fetch cancelled by user for:[/warning] {url_to_fetch}"
            )
        return WebFetchPluginOutput(
            url=url_to_fetch, content=None, error=error_message, status_code=None, truncated=False
        )

    console.print(f"[info]Fetching content from:[/info] {url_to_fetch}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url_to_fetch, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses

            content = response.text
            truncated = False
            if len(content) > MAX_CONTENT_LENGTH:
                content = content[:MAX_CONTENT_LENGTH]
                truncated = True
                console.print(
                    f"[warning]Content truncated to {MAX_CONTENT_LENGTH} characters.[/warning]"
                )

            logger.info(
                f"Successfully fetched URL: {url_to_fetch} (Status: {response.status_code}, Truncated: {truncated})"
            )
            console.print(
                f"[success]Successfully fetched URL:[/success] {url_to_fetch} [dim](Status: {response.status_code})[/dim]"
            )
            return WebFetchPluginOutput(
                url=url_to_fetch,
                content=content,
                error=None,
                status_code=response.status_code,
                truncated=truncated,
            )

    except httpx.TimeoutException:
        err_msg = f"Error: Request to {url_to_fetch} timed out after {REQUEST_TIMEOUT} seconds."
        logger.error(err_msg)
        console.print(f"[error]{err_msg}[/error]")
        return WebFetchPluginOutput(
            url=url_to_fetch, content=None, error=err_msg, status_code=None, truncated=False
        )
    except httpx.RequestError as e:
        err_msg = f"Error: An HTTP request error occurred while fetching {url_to_fetch}: {e}"
        logger.error(err_msg, exc_info=True)
        console.print(f"[error]{err_msg}[/error]")
        return WebFetchPluginOutput(
            url=url_to_fetch, content=None, error=err_msg, status_code=None, truncated=False
        )
    except httpx.HTTPStatusError as e:
        err_msg = f"Error: HTTP status error for {url_to_fetch}: {e.response.status_code} - {e.response.text[:200]}..."
        logger.error(err_msg, exc_info=True)
        console.print(f"[error]{err_msg}[/error]")
        return WebFetchPluginOutput(
            url=url_to_fetch,
            content=None,
            error=err_msg,
            status_code=e.response.status_code,
            truncated=False,
        )
    except Exception as e:
        err_msg = f"Error: An unexpected error occurred while fetching {url_to_fetch}: {e}"
        logger.error(err_msg, exc_info=True)
        console.print(f"[error]{err_msg}[/error]")
        return WebFetchPluginOutput(
            url=url_to_fetch, content=None, error=err_msg, status_code=None, truncated=False
        )


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)
    test_console = RichConsole()

    async def run_tests():
        test_console.rule("Testing web_fetch_tool plugin")

        # Test 1: Successful fetch (requires user approval)
        test_console.print(
            "\n[bold cyan]Test 1: Successful fetch (example.com) - requires approval[/bold cyan]"
        )
        input1 = WebFetchPluginInput(url="https://example.com")
        test_console.print("Please respond 'y' to the prompt.")
        output1 = await web_fetch_tool(test_console, input1)
        test_console.print(f"Output 1: {output1}")
        assert output1.content is not None and "Example Domain" in output1.content
        assert output1.status_code == 200 and output1.error is None

        # Test 2: User denies fetch
        test_console.print(
            "\n[bold cyan]Test 2: User denies fetch (google.com) - requires denial[/bold cyan]"
        )
        input2 = WebFetchPluginInput(url="https://www.google.com")
        test_console.print("Please respond 'n' to the prompt.")
        output2 = await web_fetch_tool(test_console, input2)
        test_console.print(f"Output 2: {output2}")
        assert output2.content is None and "denied by user" in output2.error

        # Test 3: Non-existent domain/connection error
        test_console.print(
            "\n[bold cyan]Test 3: Non-existent domain (nonexistent.invalid) - requires approval[/bold cyan]"
        )
        input3 = WebFetchPluginInput(url="http://nonexistent.invalid")
        test_console.print("Please respond 'y' to the prompt.")
        output3 = await web_fetch_tool(test_console, input3)
        test_console.print(f"Output 3: {output3}")
        assert output3.content is None and "RequestError" in output3.error

        # Test 4: HTTP 404 Not Found
        test_console.print(
            "\n[bold cyan]Test 4: HTTP 404 Not Found (example.com/404) - requires approval[/bold cyan]"
        )
        input4 = WebFetchPluginInput(url="https://example.com/nonexistent-page")
        test_console.print("Please respond 'y' to the prompt.")
        output4 = await web_fetch_tool(test_console, input4)
        test_console.print(f"Output 4: {output4}")
        assert output4.content is None and output4.status_code == 404
        assert "HTTP status error" in output4.error

        # Test 5: Empty URL
        test_console.print("\n[bold cyan]Test 5: Empty URL[/bold cyan]")
        input5 = WebFetchPluginInput(url="")
        output5 = await web_fetch_tool(test_console, input5)
        test_console.print(f"Output 5: {output5}")
        assert output5.content is None and "Empty URL provided" in output5.error

        # Test 6: Timeout (this might take a while if the URL actually exists and is slow)
        # For a real test, you'd need a mock server that delays response.
        # For now, using a known slow endpoint or a very short timeout.
        test_console.print(
            "\n[bold cyan]Test 6: Timeout (using a short timeout for demonstration) - requires approval[/bold cyan]"
        )
        # Note: This URL might not always timeout, depending on network conditions.
        # A better test would involve a local mock server that introduces delay.
        input6 = WebFetchPluginInput(url="http://httpbin.org/delay/5") # Delays for 5 seconds
        # Temporarily override REQUEST_TIMEOUT for this test to be shorter than 5s
        global REQUEST_TIMEOUT
        original_timeout = REQUEST_TIMEOUT
        REQUEST_TIMEOUT = 1 # Set to 1 second for this test
        test_console.print("Please respond 'y' to the prompt.")
        output6 = await web_fetch_tool(test_console, input6)
        REQUEST_TIMEOUT = original_timeout # Restore original timeout
        test_console.print(f"Output 6: {output6}")
        assert output6.content is None and "timed out" in output6.error

        # Test 7: Content truncation (using a large page)
        test_console.print(
            "\n[bold cyan]Test 7: Content truncation (wikipedia.org) - requires approval[/bold cyan]"
        )
        input7 = WebFetchPluginInput(url="https://en.wikipedia.org/wiki/Large_Hadron_Collider")
        test_console.print("Please respond 'y' to the prompt.")
        output7 = await web_fetch_tool(test_console, input7)
        test_console.print(f"Output 7: {output7}")
        assert output7.content is not None and output7.truncated is True
        assert len(output7.content) == MAX_CONTENT_LENGTH
        assert output7.status_code == 200 and output7.error is None

        test_console.rule("Web_fetch_tool tests finished.")

    asyncio.run(run_tests())

