#!/usr/bin/env python3

# Copyright notice.

from abc import ABC, abstractmethod
from typing import Any

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Common mixin classes for shared functionality across the Yesman-Claude project.

These mixins provide standardized interfaces for common patterns:
- Statistics collection and reporting
- Status and activity management
- Layout creation and updates
"""


class StatisticsProviderMixin(ABC):
    """Mixin for classes that provide statistics information."""

    @abstractmethod
    def get_statistics(self) -> dict[str, Any]:
        """Get statistics information from the implementing class.

        Returns:
            dict[str, Any]: Dictionary containing statistics data.
                           The structure depends on the implementing class.

        Example:
            {
                "total_processed": 1000,
                "success_count": 950,
                "error_count": 50,
                "processing_rate": 10.5,
                "last_updated": "2025-07-16T10:30:00"
            }
        """
        msg = "Subclasses must implement get_statistics()"
        raise NotImplementedError(msg)


class StatusManagerMixin(ABC):
    """Mixin for status and activity management."""

    @abstractmethod
    def update_status(self, status: str) -> None:
        """Update the current status.

        Args:
            status: The new status to set. Common values include:
                   "running", "stopped", "paused", "error", "initializing"

        Raises:
            ValueError: If the status value is invalid
        """
        msg = "Subclasses must implement update_status()"
        raise NotImplementedError(msg)

    @abstractmethod
    def update_activity(self, activity: str) -> None:
        """Update the current activity description.

        Args:
            activity: Description of the current activity being performed.
                     Should be a human-readable string.

        Example:
            update_activity("Processing batch 5 of 10")
            update_activity("Waiting for user input")
        """
        msg = "Subclasses must implement update_activity()"
        raise NotImplementedError(msg)


class LayoutManagerMixin(ABC):
    """Mixin for layout management in UI components."""

    @abstractmethod
    def create_layout(self) -> object:
        """Create and return a layout object.

        Returns:
            Any: The layout object. Type depends on the UI framework being used.
                For console apps, this might be a Layout object.
                For web apps, this might be a dictionary describing the layout.
        """
        msg = "Subclasses must implement create_layout()"
        raise NotImplementedError(msg)

    @abstractmethod
    def update_layout(self, layout: object) -> None:
        """Update an existing layout with new configuration or content.

        Args:
            layout: The layout object to update. Type should match what
                   create_layout() returns.

        Raises:
            TypeError: If the layout type doesn't match expected type
            ValueError: If the layout configuration is invalid
        """
        msg = "Subclasses must implement update_layout()"
        raise NotImplementedError(msg)


# Optional: Concrete mixin implementations with default behavior
class DefaultStatisticsProviderMixin(StatisticsProviderMixin):
    """Default implementation of StatisticsProviderMixin with basic
    functionality.
    """

    def __init__(self) -> None:
        self._statistics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
        }

    def get_statistics(self) -> dict[str, Any]:
        """Get current statistics with calculated success rate.

        Returns:
        dict[str, Any]: Dictionary containing statistics with calculated success rate.
        """
        stats = self._statistics.copy()
        total = stats["total_operations"]
        if total > 0:
            stats["success_rate"] = int((stats["successful_operations"] / total) * 100)
        else:
            stats["success_rate"] = 0
        return stats

    def _increment_stat(self, stat_name: str, value: int = 1) -> None:
        """Helper method to increment statistics counters."""
        if stat_name in self._statistics:
            self._statistics[stat_name] += value


class DefaultStatusManagerMixin(StatusManagerMixin):
    """Default implementation of StatusManagerMixin with basic
    functionality.
    """

    VALID_STATUSES = {"running", "stopped", "paused", "error", "initializing", "idle"}

    def __init__(self) -> None:
        self._status = "idle"
        self._activity = "No activity"

    def update_status(self, status: str) -> None:
        """Update status with validation."""
        if status not in self.VALID_STATUSES:
            msg = f"Invalid status: {status}. Must be one of {self.VALID_STATUSES}"
            raise ValueError(msg)
        self._status = status

    def update_activity(self, activity: str) -> None:
        """Update current activity description."""
        if not activity or not isinstance(activity, str):
            msg = "Activity must be a non-empty string"
            raise ValueError(msg)
        self._activity = activity

    @property
    def current_status(self) -> str:
        """Get current status.

        Returns:
        str: Description of return value.
        """
        return self._status

    @property
    def current_activity(self) -> str:
        """Get current activity.

        Returns:
        str: Description of return value.
        """
        return self._activity
