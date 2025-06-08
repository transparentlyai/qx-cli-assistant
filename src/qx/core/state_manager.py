import os
import asyncio


class DetailsManager:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DetailsManager, cls).__new__(cls)
            cls._instance._show_details_override = None
        return cls._instance

    async def is_active(self) -> bool:
        async with self._lock:
            # If an override is set, use it; otherwise check environment
            if self._show_details_override is not None:
                return self._show_details_override
            return os.getenv("QX_SHOW_DETAILS", "true").lower() == "true"

    async def set_status(self, new_status: bool):
        async with self._lock:
            self._show_details_override = new_status
            os.environ["QX_SHOW_DETAILS"] = str(new_status).lower()


details_manager = DetailsManager()
