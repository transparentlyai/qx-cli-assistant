#!/usr/bin/env python3
"""
Simple test to debug async issues
"""
import asyncio
import logging
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set environment variables
os.environ["QX_LOG_LEVEL"] = "DEBUG"
os.environ["OPENROUTER_API_KEY"] = os.environ.get("OPENROUTER_API_KEY", "test-key")
os.environ["QX_MODEL_NAME"] = "openai/gpt-3.5-turbo"

async def test_basic_async():
    """Test basic async functionality"""
    logger.info("Starting basic async test")
    
    # Test asyncio lock
    lock = asyncio.Lock()
    logger.info("Created lock")
    
    async with lock:
        logger.info("Acquired lock")
        await asyncio.sleep(0.1)
    
    logger.info("Released lock")
    
    # Test timeout
    try:
        async with asyncio.timeout(1.0):
            logger.info("In timeout context")
            await asyncio.sleep(0.1)
        logger.info("Timeout succeeded")
    except asyncio.TimeoutError:
        logger.error("Timeout failed")
    
    logger.info("Basic async test completed")

async def test_llm_components():
    """Test LLM components"""
    try:
        logger.info("Testing LLM components")
        
        # Import after setting env vars
        from qx.cli.console import qx_console
        from qx.core.mcp_manager import MCPManager
        from qx.core.llm import initialize_llm_agent
        
        logger.info("Imports successful")
        
        # Create MCP manager
        mcp_manager = MCPManager(qx_console, parent_task_group=None)
        logger.info("Created MCP manager")
        
        # Initialize agent
        agent = initialize_llm_agent(
            model_name_str="openai/gpt-3.5-turbo",
            console=qx_console,
            mcp_manager=mcp_manager,
            enable_streaming=False  # Disable streaming for test
        )
        
        if agent:
            logger.info("Agent initialized successfully")
        else:
            logger.error("Failed to initialize agent")
            
    except Exception as e:
        logger.error(f"Error testing LLM components: {e}", exc_info=True)

async def main():
    """Main test function"""
    logger.info("=== Starting async debug test ===")
    
    await test_basic_async()
    await test_llm_components()
    
    logger.info("=== Async debug test completed ===")

if __name__ == "__main__":
    asyncio.run(main())