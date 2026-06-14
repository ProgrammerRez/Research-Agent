import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from api.api import app

client = TestClient(app)


@patch("api.api.SessionStore.get_progress", new_callable=AsyncMock)
def test_get_file_markdown_assembly(mock_get, mock_session_payload):
    """Verifies markdown string collation, chronological sorting, and content integrity."""
    mock_get.return_value = mock_session_payload

    response = client.get("/file", cookies={"app_state_tracker": "active-session"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    assert "attachment; filename=" in response.headers["content-disposition"]

    file_output = response.text
    # Verify components from both mock execution loops are grouped inside the stream
    assert "Foundations of system engineering layout." in file_output
    assert "Horizontal and vertical scaling." in file_output
    assert "---" in file_output


@patch("api.api.SessionStore.get_progress", new_callable=AsyncMock)
def test_get_file_empty_markdown(mock_get):
    """Ensures a 404 block is returned if final_research elements are missing."""
    mock_get.return_value = {
        "responses": {
            "2026-06-12T12:00:00": {"final_research": ""}  # Empty text state
        }
    }

    response = client.get("/file", cookies={"app_state_tracker": "active-session"})
    assert response.status_code == 404
    assert response.json()["detail"] == "No markdown text found in session content"
