#!/usr/bin/env python3
"""
Debug the hanging issue
"""
import asyncio
import logging
import os
import sys

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/qx_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Set environment variables
os.environ["QX_LOG_LEVEL"] = "DEBUG"
os.environ["OPENROUTER_API_KEY"] = os.environ.get("OPENROUTER_API_KEY", "test-key")
os.environ["QX_MODEL_NAME"] = "openai/gpt-3.5-turbo"

async def test_llm_query():
    """Test a simple LLM query"""
    try:
        logger.info("=== Starting LLM query test ===")
        
        from qx.cli.console import qx_console
        from qx.core.mcp_manager import MCPManager
        from qx.core.llm import initialize_llm_agent, query_llm
        
        logger.info("Creating MCP manager")
        mcp_manager = MCPManager(qx_console, parent_task_group=None)
        
        logger.info("Initializing LLM agent")
        agent = initialize_llm_agent(
            model_name_str="openai/gpt-3.5-turbo",
            console=qx_console,
            mcp_manager=mcp_manager,
            enable_streaming=False  # Disable streaming for simpler test
        )
        
        if not agent:
            logger.error("Failed to initialize agent")
            return
            
        logger.info("Agent initialized, attempting query")
        
        # Try a simple query
        result = await query_llm(
            agent,
            "Hello",
            console=qx_console,
            message_history=None
        )
        
        logger.info(f"Query result: {result}")
        
        if hasattr(agent, 'cleanup'):
            await agent.cleanup()
            
    except Exception as e:
        logger.error(f"Error in test: {e}", exc_info=True)

async def main():
    """Main function"""
    await test_llm_query()

if __name__ == "__main__":
    logger.info("Starting test script")
    asyncio.run(main())
    logger.info("Test script completed")