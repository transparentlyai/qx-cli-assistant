#!/usr/bin/env python3
"""
Minimal test to check if basic components work
"""
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

# Test the session manager issue
async def test_session_manager():
    from qx.core.session_manager import save_session, reset_session
    
    print("Testing session manager...")
    
    # Test saving an empty session
    save_session([])
    
    # Test resetting
    reset_session()
    
    print("Session manager test passed")

# Test asyncio lock issue
async def test_lock():
    lock = asyncio.Lock()
    print("Testing asyncio lock...")
    
    async with lock:
        print("Lock acquired")
        await asyncio.sleep(0.1)
    
    print("Lock released")
    print("Lock test passed")

async def main():
    await test_session_manager()
    await test_lock()

if __name__ == "__main__":
    asyncio.run(main())