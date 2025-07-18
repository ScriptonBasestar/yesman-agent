#!/usr/bin/env python3
"""Async-capable base command class for long-running operations."""

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any

from .base_command import BaseCommand, CommandError


class AsyncBaseCommand(BaseCommand, ABC):
    """Async-capable base class for commands with long-running operations."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._running = False
        self._loop = None

    @abstractmethod
    async def execute_async(self, **kwargs) -> dict:
        """Async version of execute method - must be implemented by subclasses."""
        pass

    def execute(self, **kwargs) -> dict:
        """Sync wrapper that runs the async execute method."""
        try:
            # Use existing event loop if available, otherwise create new one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're already in an async context, use run_coroutine_threadsafe directly
                    coro = self.execute_async(**kwargs)
                    return asyncio.run_coroutine_threadsafe(coro, loop).result()
                else:
                    return loop.run_until_complete(self.execute_async(**kwargs))
            except RuntimeError:
                # No event loop exists, create a new one
                return asyncio.run(self.execute_async(**kwargs))
        except Exception as e:
            if isinstance(e, CommandError):
                raise
            raise CommandError(f"Async command execution failed: {e}") from e

    async def sleep(self, duration: float) -> None:
        """Async sleep wrapper for better concurrency."""
        await asyncio.sleep(duration)

    async def run_with_interval(self, async_func: Callable[[], Coroutine[Any, Any, None]], interval: float, max_iterations: int | None = None) -> None:
        """Run an async function repeatedly with specified interval."""
        self._running = True
        iterations = 0

        try:
            while self._running:
                if max_iterations and iterations >= max_iterations:
                    break

                await async_func()
                await self.sleep(interval)
                iterations += 1

        except asyncio.CancelledError:
            self.logger.info("Async operation cancelled")
            self._running = False
            raise
        except Exception as e:
            self.logger.error(f"Error in async loop: {e}")
            self._running = False
            raise CommandError(f"Async operation failed: {e}") from e

    def stop(self) -> None:
        """Stop the running async operation."""
        self._running = False

    @property
    def is_running(self) -> bool:
        """Check if async operation is running."""
        return self._running


class AsyncMonitoringMixin:
    """Mixin for commands that need monitoring capabilities."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_interval = 1.0  # Default 1 second
        self._monitor_data = {}

    # Type hints for methods from BaseCommand that will be available when mixed
    print_info: Callable[[str], None]
    print_success: Callable[[str], None]
    print_error: Callable[[str], None]
    print_warning: Callable[[str], None]
    stop: Callable[[], None]
    run_with_interval: Callable

    async def start_monitoring(self, update_func: Callable[[], Coroutine[Any, Any, None]] | None = None) -> None:
        """Start monitoring with regular updates."""
        if not isinstance(self, AsyncBaseCommand):
            raise CommandError("AsyncMonitoringMixin requires AsyncBaseCommand")

        update_function = update_func or self.update_monitoring_data

        try:
            await self.run_with_interval(update_function, self.update_interval)
        except KeyboardInterrupt:
            self.print_info("\n📊 Monitoring stopped by user")
            self.stop()

    async def update_monitoring_data(self) -> None:
        """Override this method to implement specific monitoring logic."""
        pass

    def set_update_interval(self, interval: float) -> None:
        """Set the monitoring update interval."""
        if interval <= 0:
            raise CommandError("Update interval must be positive")
        self.update_interval = interval


class AsyncProgressMixin:
    """Mixin for commands that need progress reporting."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._progress_total = 0
        self._progress_current = 0

    # Type hints for methods from BaseCommand that will be available when mixed
    print_info: Callable[[str], None]
    print_success: Callable[[str], None]
    print_error: Callable[[str], None]

    async def with_progress(self, async_func: Callable[[], Coroutine[Any, Any, Any]], total_steps: int, description: str = "Processing") -> Any:
        """Execute async function with progress tracking."""
        self._progress_total = total_steps
        self._progress_current = 0

        self.print_info(f"🚀 {description}...")

        try:
            result = await async_func()
            self.print_success(f"✅ {description} completed")
            return result
        except Exception as e:
            self.print_error(f"❌ {description} failed: {e}")
            raise

    async def update_progress(self, step: int = 1, message: str = None) -> None:
        """Update progress counter."""
        self._progress_current += step
        progress_pct = (self._progress_current / self._progress_total) * 100

        progress_msg = f"Progress: {self._progress_current}/{self._progress_total} ({progress_pct:.1f}%)"
        if message:
            progress_msg += f" - {message}"

        self.print_info(progress_msg)

    def reset_progress(self) -> None:
        """Reset progress counters."""
        self._progress_total = 0
        self._progress_current = 0


class AsyncRetryMixin:
    """Mixin for commands that need retry capabilities."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = 3
        self.retry_delay = 1.0
        self.backoff_multiplier = 2.0

    # Type hints for methods from BaseCommand that will be available when mixed
    print_warning: Callable[[str], None]
    print_error: Callable[[str], None]

    async def with_retry(
        self,
        async_func: Callable[[], Coroutine[Any, Any, Any]],
        max_retries: int = None,
        retry_delay: float = None,
        backoff_multiplier: float = None,
    ) -> Any:
        """Execute async function with exponential backoff retry."""
        max_retries = max_retries or self.max_retries
        retry_delay = retry_delay or self.retry_delay
        backoff_multiplier = backoff_multiplier or self.backoff_multiplier

        last_exception = None
        current_delay = retry_delay

        for attempt in range(max_retries + 1):
            try:
                return await async_func()
            except Exception as e:
                last_exception = e

                if attempt < max_retries:
                    self.print_warning(f"⚠️  Attempt {attempt + 1} failed: {e}. Retrying in {current_delay:.1f}s...")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_multiplier
                else:
                    self.print_error(f"❌ All {max_retries + 1} attempts failed")

        # If we get here, all retries failed
        raise CommandError(
            f"Operation failed after {max_retries + 1} attempts",
            recovery_hint="Check your configuration and network connectivity",
        ) from last_exception

    def set_retry_config(
        self,
        max_retries: int = None,
        retry_delay: float = None,
        backoff_multiplier: float = None,
    ) -> None:
        """Configure retry behavior."""
        if max_retries is not None:
            self.max_retries = max_retries
        if retry_delay is not None:
            self.retry_delay = retry_delay
        if backoff_multiplier is not None:
            self.backoff_multiplier = backoff_multiplier


# Convenience base classes combining common mixins
class AsyncMonitoringCommand(AsyncBaseCommand, AsyncMonitoringMixin):
    """Base class for async monitoring commands."""

    pass


class AsyncProgressCommand(AsyncBaseCommand, AsyncProgressMixin):
    """Base class for async commands with progress tracking."""

    pass


class AsyncRetryCommand(AsyncBaseCommand, AsyncRetryMixin):
    """Base class for async commands with retry capabilities."""

    pass


class AsyncFullFeaturedCommand(AsyncBaseCommand, AsyncMonitoringMixin, AsyncProgressMixin, AsyncRetryMixin):
    """Base class for async commands with all features."""

    pass
