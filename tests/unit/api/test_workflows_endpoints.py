# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Test for FastAPI workflows endpoints."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from api.main import app


class TestWorkflowsEndpoints(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    @patch("api.routers.workflows.container")
    def test_get_workflow_templates(self, mock_container: object) -> None:
        """Test GET /workflows/templates returns template list."""
        # Setup mock
        mock_service = MagicMock()
        mock_service.list_templates.return_value = {
            "template1": {
                "id": "template1",
                "name": "Test Template",
                "description": "A test template",
            },
        }
        mock_container.resolve.return_value = mock_service

        # Make request
        response = self.client.get("/workflows/templates")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch("api.routers.workflows.container")
    def test_start_workflow_execution(self, mock_container: object) -> None:
        """Test POST /workflows/executions starts workflow."""
        # Setup mock
        mock_service = MagicMock()
        mock_service.start_workflow = AsyncMock(return_value="exec-123")
        mock_service.get_execution.return_value = MagicMock(
            id="exec-123",
            template_id="template1",
            status=MagicMock(value="running"),
            current_step=0,
            progress=0.0,
            created_at=None,
            started_at=None,
            completed_at=None,
        )
        mock_container.resolve.return_value = mock_service

        # Make request
        response = self.client.post(
            "/workflows/executions",
            json={
                "template_id": "template1",
                "context": {"key": "value"},
            },
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["template_id"] == "template1"

    @patch("api.routers.workflows.container")
    def test_get_workflow_executions(self, mock_container: object) -> None:
        """Test GET /workflows/executions returns execution list."""
        # Setup mock
        mock_service = MagicMock()
        mock_execution = MagicMock(
            id="exec-123",
            template_id="template1",
            status=MagicMock(value="completed"),
            current_step=5,
            progress=100.0,
            created_at=None,
            started_at=None,
            completed_at=None,
        )
        mock_service.list_executions.return_value = [mock_execution]
        mock_container.resolve.return_value = mock_service

        # Make request
        response = self.client.get("/workflows/executions")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    unittest.main()
