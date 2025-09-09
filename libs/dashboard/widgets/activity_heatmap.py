"""Activity heatmap widget for dashboard."""

from typing import Any


class ActivityHeatmapGenerator:
    """Generates activity heatmap data for dashboard visualization."""

    def __init__(self, config=None):
        self.config = config

    def generate_heatmap_data(self, days: int = 30) -> dict[str, Any]:
        """Generate heatmap data for the specified number of days."""
        return {"data": [], "max_value": 0, "period": days, "generated_at": "now"}

    def get_activity_summary(self) -> dict[str, Any]:
        """Get activity summary for the heatmap."""
        return {"total_sessions": 0, "active_days": 0, "avg_session_length": 0}
