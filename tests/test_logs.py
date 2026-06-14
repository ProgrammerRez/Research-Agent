import pytest
import orjson
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from api.api import app

client = TestClient(app)


@patch("api.api.SessionStore.get_progress", new_callable=AsyncMock)
def test_get_logs_success(mock_get, mock_session_payload):
    """Verifies that individual audit logs are correctly joined via newlines."""
    mock_get.return_value = mock_session_payload

    response = client.get("/logs", cookies={"app_state_tracker": "session-id-123"})

    assert response.status_code == 200
    assert "attachment; filename=" in response.headers["content-disposition"]

    # Note: Your implementation passes strings directly through orjson.dumps,
    # meaning the output stream returns valid JSON bytes representing a string wrapper.
    parsed_string = orjson.loads(response.content)
    assert "Successfully ran workflow" in parsed_string
    assert "\n" in parsed_string


@patch("api.api.SessionStore.get_progress", new_callable=AsyncMock)
def test_get_logs_missing_session(mock_get):
    """Verifies log extraction failure management states."""
    mock_get.return_value = None

    response = client.get("/logs", cookies={"app_state_tracker": "ghost-session"})
    assert response.status_code == 404
