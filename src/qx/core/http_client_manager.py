"""
Singleton HTTP client manager for shared connection pooling.
"""
import asyncio
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class HTTPClientManager:
    """Manages a shared HTTP client instance for connection pooling."""
    
    _instance: Optional['HTTPClientManager'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._client: Optional[httpx.AsyncClient] = None
            self._initialized = True
    
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create the shared HTTP client."""
        async with self._lock:
            if self._client is None:
                logger.info("Creating shared HTTP client")
                self._client = httpx.AsyncClient(
                    timeout=httpx.Timeout(60.0, connect=10.0),
                    limits=httpx.Limits(
                        max_connections=20,
                        max_keepalive_connections=10,
                        keepalive_expiry=30.0
                    ),
                    follow_redirects=True,
                    http2=True  # Enable HTTP/2 for better performance
                )
            return self._client
    
    async def cleanup(self):
        """Clean up the HTTP client."""
        async with self._lock:
            if self._client:
                logger.info("Closing shared HTTP client")
                await self._client.aclose()
                self._client = None


# Global instance
http_client_manager = HTTPClientManager()