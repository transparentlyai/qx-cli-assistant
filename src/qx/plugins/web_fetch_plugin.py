import logging
from typing import Optional

import httpx
from pydantic import BaseModel, Field
from rich.console import Console as RichConsole

from qx.core.workflow_approval import create_workflow_aware_approval_handler
from qx.core.http_client_manager import http_client_manager
from qx.cli.console import themed_console

logger = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 550000
REQUEST_TIMEOUT = 10


class WebFetchPluginInput(BaseModel):
    url: str = Field(..., description="The URL to fetch content from.")
    format: str = Field("markdown", description="Output format: 'markdown' or 'raw'.")


class WebFetchPluginOutput(BaseModel):
    url: str
    content: Optional[str] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    truncated: bool = False


async def web_fetch_tool(
    console: RichConsole, args: WebFetchPluginInput
) -> WebFetchPluginOutput:
    approval_handler = await create_workflow_aware_approval_handler(themed_console)
    url = args.url.strip()
    output_format = args.format.lower()

    if not url:
        err_msg = "Empty URL provided."
        themed_console.print(f"Web Fetch (Error): {err_msg}")
        return WebFetchPluginOutput(url="", error=err_msg)

    if output_format not in ["markdown", "raw"]:
        err_msg = f"Invalid format '{output_format}'. Use 'markdown' or 'raw'."
        themed_console.print(f"Web Fetch (Error): {err_msg}")
        return WebFetchPluginOutput(url=url, error=err_msg)

    status, _ = await approval_handler.request_approval(
        operation="Web Fetch",
        parameter_name="url",
        parameter_value=url,
        prompt_message=f"Allow [primary]Qx[/] to fetch content from: [highlight]'{url}'[/]?",
    )

    if status not in ["approved", "session_approved"]:
        err_msg = "Operation denied by user."
        approval_handler.print_outcome("Fetch", "Denied by user.", success=False)
        return WebFetchPluginOutput(url=url, error=err_msg)

    try:
        client = await http_client_manager.get_client()
        response = await client.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        content = response.text
        truncated = False
        if len(content) > MAX_CONTENT_LENGTH:
            content = content[:MAX_CONTENT_LENGTH]
            truncated = True
            themed_console.print("  └─ Note: Content truncated.")

        final_content = content
        if output_format == "markdown":
            try:
                from markdownify import markdownify as md  # type: ignore

                final_content = md(content)
            except ImportError:
                approval_handler.print_outcome(
                    "Conversion",
                    "Failed. `markdownify` not installed.",
                    success=False,
                )
            except Exception as e:
                approval_handler.print_outcome(
                    "Conversion", f"Failed. {e}", success=False
                )

        approval_handler.print_outcome("Fetch", "Successfully completed.")
        return WebFetchPluginOutput(
            url=url,
            content=final_content,
            status_code=response.status_code,
            truncated=truncated,
        )

    except httpx.HTTPStatusError as e:
        err_msg = f"HTTP {e.response.status_code} error for {url}"
        approval_handler.print_outcome("Fetch", err_msg, success=False)
        return WebFetchPluginOutput(
            url=url, error=err_msg, status_code=e.response.status_code
        )
    except Exception as e:
        err_msg = f"An unexpected error occurred: {e}"
        approval_handler.print_outcome("Fetch", err_msg, success=False)
        return WebFetchPluginOutput(url=url, error=err_msg)
