import logging
from typing import Optional

import httpx
from pydantic import BaseModel, Field
from rich.console import Console as RichConsole

# Removed: from qx.core.user_prompts import request_confirmation

logger = logging.getLogger(__name__)

# Constants
MAX_CONTENT_LENGTH = 250000  # Max characters to return from a fetched page
REQUEST_TIMEOUT = 10  # seconds


class WebFetchPluginInput(BaseModel):
    """Input model for the WebFetchTool."""

    url: str = Field(
        ...,
        description="The URL to fetch content from. Must be a valid HTTP/HTTPS URL.",
    )
    format: str = Field(
        "markdown",
        description="Output format: 'markdown' (default, converts HTML to Markdown) or 'raw' (returns content as-is).",
    )


class WebFetchPluginOutput(BaseModel):
    """Output model for the WebFetchTool."""

    url: str = Field(description="The URL that was attempted to be fetched.")
    content: Optional[str] = Field(
        None,
        description="The fetched content (in requested format). None if fetch failed or was denied.",
    )
    error: Optional[str] = Field(
        None,
        description="Error message explaining why fetch failed (e.g., 'timeout', 'HTTP error', 'denied by user'). None if successful.",
    )
    status_code: Optional[int] = Field(
        None,
        description="HTTP response status code (e.g., 200, 404). None if request failed before receiving response.",
    )
    truncated: bool = Field(
        False,
        description="True if content was truncated to 250,000 characters due to size limits.",
    )


async def web_fetch_tool(
    console: RichConsole, args: WebFetchPluginInput
) -> WebFetchPluginOutput:
    """
    Fetches content from a specified URL.

    Features:
    - Approval is handled by the terminal layer.
    - Supports HTML to Markdown conversion (default)
    - 10-second timeout for requests
    - Content truncated at 250,000 characters if needed
    - Handles HTTP errors gracefully

    Output formats:
    - 'markdown': Converts HTML to Markdown for readability
    - 'raw': Returns content exactly as received

    Returns structured output with:
    - url: The attempted URL
    - content: Fetched content (if successful)
    - error: Error details (if failed)
    - status_code: HTTP response code
    - truncated: Whether content was truncated
    """
    url_to_fetch = args.url.strip()
    output_format = args.format.lower()

    if not url_to_fetch:
        err_msg = "Error: Empty URL provided."
        logger.error(err_msg)
        console.print(f"[error]{err_msg}[/]")
        return WebFetchPluginOutput(
            url="", content=None, error=err_msg, status_code=None, truncated=False
        )

    if output_format not in ["markdown", "raw"]:
        err_msg = f"Error: Invalid format '{output_format}'. Supported formats are 'markdown' and 'raw'."
        logger.error(err_msg)
        console.print(f"[error]{err_msg}[/]")
        return WebFetchPluginOutput(
            url=url_to_fetch,
            content=None,
            error=err_msg,
            status_code=None,
            truncated=False,
        )

    # Approval is now assumed to be handled by the terminal layer.
    console.print(f"[info]Fetching content from:[/info] [info]'{url_to_fetch}'[/]")

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(url_to_fetch)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses

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
                try:
                    from markdownify import markdownify as md_converter  # type: ignore

                    final_content = md_converter(content)
                except ImportError:
                    logger.warning(
                        "markdownify not installed. Cannot convert to markdown. Returning raw content."
                    )
                    # final_content remains content (raw)
                except Exception as e:
                    logger.warning(
                        f"Could not convert content to markdown: {e}. Returning raw content."
                    )
                    # final_content remains content (raw)

            logger.debug(
                f"Successfully fetched URL: {url_to_fetch} (Status: {response.status_code}, Truncated: {truncated})"
            )
            console.print(
                f"[success]Successfully fetched URL:[/success] [success]{url_to_fetch}[/] [dim](Status: {response.status_code})[/dim]"
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
        console.print(f"[error]{err_msg}[/]")
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
        console.print(f"[error]{err_msg}[/]")
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
        console.print(f"[error]{err_msg}[/]")
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
        console.print(f"[error]{err_msg}[/]")
        return WebFetchPluginOutput(
            url=url_to_fetch,
            content=None,
            error=err_msg,
            status_code=None,
            truncated=False,
        )
