# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Test for FastAPI dashboard endpoints."""

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from api.main import app


class TestDashboardEndpoints(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    @patch("api.routers.dashboard.get_tmux_manager")
    def test_get_dashboard_sessions(self, mock_get_tmux: object) -> None:
        """Test GET /api/dashboard/sessions returns session list."""
        # Setup mock
        mock_tm = MagicMock()
        mock_tm.list_sessions.return_value = [
            {"name": "test-session", "windows": 2, "attached": 1},
        ]
        mock_get_tmux.return_value = mock_tm

        # Make request
        response = self.client.get("/api/dashboard/sessions")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert len(data["sessions"]) == 1

    @patch("api.routers.dashboard.health_calculator")
    def test_get_dashboard_health(self, mock_health_calc: object) -> None:
        """Test GET /api/dashboard/health returns health metrics."""
        # Setup mock
        mock_health_calc.calculate_overall_health.return_value = {
            "overall_score": 85.0,
            "status": "healthy",
            "components": {
                "system": {"score": 90.0, "status": "healthy"},
                "sessions": {"score": 80.0, "status": "healthy"},
            },
        }

        # Make request
        response = self.client.get("/api/dashboard/health")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert data["status"] == "healthy"

    @patch("api.routers.dashboard.get_tmux_manager")
    def test_get_dashboard_stats(self, mock_get_tmux: object) -> None:
        """Test GET /api/dashboard/stats returns statistics."""
        # Setup mock
        mock_tm = MagicMock()
        mock_tm.list_sessions.return_value = [
            {"name": "session1"},
            {"name": "session2"},
        ]
        mock_get_tmux.return_value = mock_tm

        # Make request
        response = self.client.get("/api/dashboard/stats")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "total_sessions" in data


if __name__ == "__main__":
    unittest.main()
