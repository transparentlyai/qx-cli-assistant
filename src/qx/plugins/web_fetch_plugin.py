import logging
from typing import Optional

import httpx
from markitdown import MarkItDown
from pydantic import BaseModel, Field
from rich.console import Console as RichConsole

from qx.core.user_prompts import request_confirmation

logger = logging.getLogger(__name__)

# Constants
MAX_CONTENT_LENGTH = 250000  # Max characters to return from a fetched page
REQUEST_TIMEOUT = 10  # seconds


class WebFetchPluginInput(BaseModel):
    """Input model for the WebFetchTool."""

    url: str = Field(
        ...,
        description="The URL of the web page to fetch content from. Must be a valid and accessible URL.",
    )
    format: str = Field(
        "markdown",
        description="The desired output format for the fetched content. Can be 'markdown' (default) to convert HTML to Markdown, or 'raw' to return the content as-is.",
    )


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
        False,
        description="True if the fetched content was truncated to MAX_CONTENT_LENGTH due to its original size exceeding the limit.",
    )


async def web_fetch_tool(
    console: RichConsole, args: WebFetchPluginInput
) -> WebFetchPluginOutput:
    """
    Fetches content from a specified URL on the internet.

    This tool requires explicit user confirmation for security reasons before accessing any external URL.
    The fetched content can be returned in either 'markdown' format (default, where HTML is converted to Markdown)
    or 'raw' format (the original content as received).
    """
    url_to_fetch = args.url.strip()
    output_format = args.format.lower()

    if not url_to_fetch:
        err_msg = "Error: Empty URL provided."
        logger.error(err_msg)
        console.print(f"[red]{err_msg}[/red]")
        return WebFetchPluginOutput(
            url="", content=None, error=err_msg, status_code=None, truncated=False
        )

    if output_format not in ["markdown", "raw"]:
        err_msg = f"Error: Invalid format '{output_format}'. Supported formats are 'markdown' and 'raw'."
        logger.error(err_msg)
        console.print(f"[red]{err_msg}[/red]")
        return WebFetchPluginOutput(
            url=url_to_fetch,
            content=None,
            error=err_msg,
            status_code=None,
            truncated=False,
        )

    console.print(
        f"[info]Requesting permission to fetch URL:[/info] [blue]'{url_to_fetch}'[/blue]"
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
        # request_confirmation already prints a message for denied/cancelled
        return WebFetchPluginOutput(
            url=url_to_fetch,
            content=None,
            error=error_message,
            status_code=None,
            truncated=False,
        )

    console.print(f"[info]Fetching content from:[/info] [blue]'{url_to_fetch}'[/blue]")

    try:
        # Use a simple HTTP client for now
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(url_to_fetch)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            # URL fetched successfully

            content = response.text
            truncated = False
            if len(content) > MAX_CONTENT_LENGTH:
                content = content[:MAX_CONTENT_LENGTH]
                truncated = True
                console.print(
                    f"[warning]Content truncated to {MAX_CONTENT_LENGTH} characters.[/warning]"
                )

            final_content = content
            if output_format == "markdown":
                md = MarkItDown()
                try:
                    from markdownify import markdownify as md_converter

                    final_content = md_converter(content)
                except ImportError:
                    logger.warning(
                        "markdownify not installed. Cannot convert to markdown. Returning raw content."
                    )
                    final_content = content
                except Exception as e:
                    logger.warning(
                        f"Could not convert content to markdown: {e}. Returning raw content."
                    )
                    final_content = content  # Fallback to raw if conversion fails

            logger.info(
                f"Successfully fetched URL: {url_to_fetch} (Status: {response.status_code}, Truncated: {truncated})"
            )
            console.print(
                f"[success]Successfully fetched URL:[/success] [green]{url_to_fetch}[/green] [dim](Status: {response.status_code})[/dim]"
            )
            return WebFetchPluginOutput(
                url=url_to_fetch,
                content=final_content,
                error=None,
                status_code=response.status_code,
                truncated=truncated,
            )

    except httpx.TimeoutException:
        err_msg = f"Error: Request to {url_to_fetch} timed out after {REQUEST_TIMEOUT} seconds."
        logger.error(err_msg)
        console.print(f"[red]{err_msg}[/red]")
        return WebFetchPluginOutput(
            url=url_to_fetch,
            content=None,
            error=err_msg,
            status_code=None,
            truncated=False,
        )
    except httpx.RequestError as e:
        err_msg = (
            f"Error: An HTTP request error occurred while fetching {url_to_fetch}: {e}"
        )
        logger.error(err_msg, exc_info=True)
        console.print(f"[red]{err_msg}[/red]")
        return WebFetchPluginOutput(
            url=url_to_fetch,
            content=None,
            error=err_msg,
            status_code=None,
            truncated=False,
        )
    except httpx.HTTPStatusError as e:
        err_msg = f"Error: HTTP status error for {url_to_fetch}: {e.response.status_code} - {e.response.text[:200]}..."
        logger.error(err_msg, exc_info=True)
        console.print(f"[red]{err_msg}[/red]")
        return WebFetchPluginOutput(
            url=url_to_fetch,
            content=None,
            error=err_msg,
            status_code=e.response.status_code,
            truncated=False,
        )
    except Exception as e:
        err_msg = (
            f"Error: An unexpected error occurred while fetching {url_to_fetch}: {e}"
        )
        logger.error(err_msg, exc_info=True)
        console.print(f"[red]{err_msg}[/red]")
        return WebFetchPluginOutput(
            url=url_to_fetch,
            content=None,
            error=err_msg,
            status_code=None,
            truncated=False,
        )
