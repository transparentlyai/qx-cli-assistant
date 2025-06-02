"""
Async utilities for robust concurrent operations.
"""

import asyncio
import functools
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, Optional, Set, TypeVar
from weakref import WeakSet

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TaskTracker:
    """Tracks and manages background tasks with proper cleanup."""

    def __init__(self):
        self._tasks: WeakSet[asyncio.Task] = WeakSet()
        self._task_names: Dict[asyncio.Task, str] = {}
        self._lock = asyncio.Lock()

    async def create_task(
        self,
        coro: Any,
        name: Optional[str] = None,
        error_handler: Optional[Callable[[Exception], None]] = None,
    ) -> asyncio.Task:
        """Create and track a task with optional error handling."""

        async def wrapped():
            try:
                return await coro
            except asyncio.CancelledError:
                logger.debug(f"Task {name or 'unnamed'} was cancelled")
                raise
            except Exception as e:
                logger.error(f"Error in task {name or 'unnamed'}: {e}", exc_info=True)
                if error_handler:
                    try:
                        error_handler(e)
                    except Exception as handler_error:
                        logger.error(
                            f"Error in error handler: {handler_error}", exc_info=True
                        )
                raise

        task = asyncio.create_task(wrapped(), name=name)

        async with self._lock:
            self._tasks.add(task)
            if name:
                self._task_names[task] = name

        def cleanup(_):
            # Clean up task references when done
            self._task_names.pop(task, None)

        task.add_done_callback(cleanup)
        return task

    async def cancel_all(self, timeout: float = 5.0) -> None:
        """Cancel all tracked tasks with timeout."""
        async with self._lock:
            tasks = list(self._tasks)

        if not tasks:
            return

        logger.info(f"Cancelling {len(tasks)} background tasks")

        # Cancel all tasks
        for task in tasks:
            if not task.done():
                task.cancel()

        # Wait for cancellation with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for {len(tasks)} tasks to cancel")

    def get_running_tasks(self) -> Set[asyncio.Task]:
        """Get set of currently running tasks."""
        return {task for task in self._tasks if not task.done()}


class CircuitBreaker:
    """Circuit breaker pattern for handling repeated failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        async with self._lock:
            if self._failure_count >= self.failure_threshold:
                if self._last_failure_time:
                    time_since_failure = time.time() - self._last_failure_time
                    if time_since_failure < self.recovery_timeout:
                        raise RuntimeError(
                            f"Circuit breaker open: {self._failure_count} failures, "
                            f"retry after {self.recovery_timeout - time_since_failure:.1f}s"
                        )
                    else:
                        # Reset after recovery timeout
                        logger.info("Circuit breaker: Resetting after recovery timeout")
                        self._failure_count = 0
                        self._last_failure_time = None
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        async with self._lock:
            if exc_type and issubclass(exc_type, self.expected_exception):
                self._failure_count += 1
                self._last_failure_time = time.time()
                logger.warning(
                    f"Circuit breaker: Failure {self._failure_count}/{self.failure_threshold}"
                )
            elif exc_type is None:
                # Success - reset failure count
                if self._failure_count > 0:
                    logger.info("Circuit breaker: Operation succeeded, resetting")
                self._failure_count = 0
                self._last_failure_time = None
        return False


class AsyncLock:
    """Enhanced async lock with timeout and debugging."""

    def __init__(self, name: str = "unnamed", timeout: float = 30.0):
        self._lock = asyncio.Lock()
        self._name = name
        self._timeout = timeout
        self._holder: Optional[asyncio.Task] = None
        self._acquire_time: Optional[float] = None

    async def __aenter__(self):
        task = asyncio.current_task()
        try:
            await asyncio.wait_for(self._lock.acquire(), timeout=self._timeout)
            self._holder = task
            self._acquire_time = time.time()
            logger.debug(
                f"Lock '{self._name}' acquired by {task.get_name() if task else 'unknown'}"
            )
            return self
        except asyncio.TimeoutError:
            logger.error(
                f"Timeout acquiring lock '{self._name}' after {self._timeout}s. "
                f"Held by: {self._holder.get_name() if self._holder else 'unknown'}"
            )
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._acquire_time:
            hold_time = time.time() - self._acquire_time
            if hold_time > 5.0:  # Warn if lock held too long
                logger.warning(
                    f"Lock '{self._name}' held for {hold_time:.1f}s by "
                    f"{self._holder.get_name() if self._holder else 'unknown'}"
                )
        self._holder = None
        self._acquire_time = None
        self._lock.release()
        logger.debug(f"Lock '{self._name}' released")
        return False


def with_timeout(timeout: float):
    """Decorator to add timeout to async functions."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                logger.error(f"Timeout in {func.__name__} after {timeout}s")
                raise

        return wrapper

    return decorator


async def safe_gather(
    *coros, return_exceptions: bool = True, timeout: Optional[float] = None
):
    """Enhanced gather with timeout and better error handling."""
    if timeout:
        try:
            return await asyncio.wait_for(
                asyncio.gather(*coros, return_exceptions=return_exceptions),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            # Cancel remaining tasks
            for coro in coros:
                if asyncio.iscoroutine(coro):
                    coro.close()
            raise
    else:
        return await asyncio.gather(*coros, return_exceptions=return_exceptions)


class AsyncResourceManager:
    """Manages async resources with proper cleanup."""

    def __init__(self):
        self._resources: Dict[str, Any] = {}
        self._cleanup_funcs: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()

    async def register(
        self, name: str, resource: Any, cleanup_func: Optional[Callable] = None
    ):
        """Register a resource with optional cleanup function."""
        async with self._lock:
            if name in self._resources:
                logger.warning(f"Resource '{name}' already registered, replacing")
                await self._cleanup_resource(name)

            self._resources[name] = resource
            if cleanup_func:
                self._cleanup_funcs[name] = cleanup_func

    async def get(self, name: str) -> Optional[Any]:
        """Get a registered resource."""
        async with self._lock:
            return self._resources.get(name)

    async def _cleanup_resource(self, name: str):
        """Clean up a single resource."""
        if name in self._cleanup_funcs:
            try:
                cleanup = self._cleanup_funcs[name]
                if asyncio.iscoroutinefunction(cleanup):
                    await cleanup(self._resources[name])
                else:
                    cleanup(self._resources[name])
            except Exception as e:
                logger.error(f"Error cleaning up resource '{name}': {e}", exc_info=True)

        self._resources.pop(name, None)
        self._cleanup_funcs.pop(name, None)

    async def cleanup_all(self):
        """Clean up all resources."""
        async with self._lock:
            names = list(self._resources.keys())

        for name in names:
            await self._cleanup_resource(name)


@asynccontextmanager
async def timeout_context(seconds: float, error_message: str = "Operation timed out"):
    """Context manager for operations with timeout."""
    try:
        async with asyncio.timeout(seconds):
            yield
    except asyncio.TimeoutError:
        logger.error(f"{error_message} after {seconds}s")
        raise


class BackpressureController:
    """Controls backpressure for streaming operations."""

    def __init__(self, max_pending: int = 100, check_interval: float = 0.1):
        self.max_pending = max_pending
        self.check_interval = check_interval
        self._pending_count = 0
        self._lock = asyncio.Lock()
        self._can_proceed = asyncio.Event()
        self._can_proceed.set()

    async def acquire(self):
        """Acquire permission to add work."""
        while True:
            async with self._lock:
                if self._pending_count < self.max_pending:
                    self._pending_count += 1
                    return

            # Wait before checking again
            await asyncio.sleep(self.check_interval)

    async def release(self):
        """Release after work is done."""
        async with self._lock:
            self._pending_count = max(0, self._pending_count - 1)
            if self._pending_count < self.max_pending:
                self._can_proceed.set()

    @property
    def pending_count(self) -> int:
        """Get current pending count."""
        return self._pending_count
