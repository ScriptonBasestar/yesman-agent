# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Test for FastAPI AI providers endpoints."""

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from api.main import app


class TestAIProvidersEndpoints(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    @patch("api.routers.ai_providers.provider_manager")
    def test_list_providers(self, mock_manager: object) -> None:
        """Test GET /ai-providers returns provider list."""
        # Setup mock
        mock_manager.list_providers.return_value = [
            {
                "type": "claude_code",
                "status": "active",
                "config": {"api_key": "***"},
            },
        ]

        # Make request
        response = self.client.get("/ai-providers/")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "type" in data[0]

    @patch("api.routers.ai_providers.provider_manager")
    def test_register_provider(self, mock_manager: object) -> None:
        """Test POST /ai-providers/register registers new provider."""
        # Setup mock
        mock_manager.register_provider.return_value = True

        # Make request
        response = self.client.post(
            "/ai-providers/register",
            json={
                "provider_type": "ollama",
                "config": {"base_url": "http://localhost:11434"},
            },
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "registered"

    @patch("api.routers.ai_providers.provider_manager")
    def test_get_provider_status(self, mock_manager: object) -> None:
        """Test GET /ai-providers/{provider_type}/status returns status."""
        # Setup mock
        mock_manager.get_provider_status.return_value = {
            "type": "claude_code",
            "status": "active",
            "health": "healthy",
            "models": ["claude-3", "claude-2"],
        }

        # Make request
        response = self.client.get("/ai-providers/claude_code/status")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "claude_code"
        assert data["status"] == "active"

    @patch("api.routers.ai_providers.task_manager")
    def test_create_ai_task(self, mock_task_manager: object) -> None:
        """Test POST /ai-providers/tasks creates new task."""
        # Setup mock
        mock_task_manager.create_task.return_value = {
            "task_id": "task-123",
            "status": "pending",
            "provider": "claude_code",
        }

        # Make request
        response = self.client.post(
            "/ai-providers/tasks",
            json={
                "provider_type": "claude_code",
                "prompt": "Test prompt",
                "context": {},
            },
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data


if __name__ == "__main__":
    unittest.main()
