import os
import asyncio


class ShowThinkingManager:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ShowThinkingManager, cls).__new__(cls)
            cls._instance._show_thinking_override = None
        return cls._instance

    async def is_active(self) -> bool:
        async with self._lock:
            # If an override is set, use it; otherwise check environment
            if self._show_thinking_override is not None:
                return self._show_thinking_override
            return os.getenv("QX_SHOW_THINKING", "true").lower() == "true"

    async def set_status(self, new_status: bool):
        async with self._lock:
            self._show_thinking_override = new_status
            os.environ["QX_SHOW_THINKING"] = str(new_status).lower()


show_thinking_manager = ShowThinkingManager()
