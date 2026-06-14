import pytest
import orjson
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from api.api import app

# 1. Creating client test object
client = TestClient(app=app)


# 2. Testing JSON Download Function
@patch("api.api.SessionStore.get_progress", new_callable=AsyncMock)
def test_json_download_file_success(mock_get, mock_session_payload):
    """Verifies the raw dictionary state is accurately serialized and streamed."""

    # 1. Getting Mock Payload
    mock_get.return_value = mock_session_payload

    # 2. Sending Payload and getting response
    response = client.get("/json", cookies={"app_state_tracker": "session_id_123"})

    # 3. Assertions
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment; filename=" in response.headers["content-disposition"]

    # 4. Parse output to verify structure validation
    streamed_data = orjson.loads(response.content)
    assert "responses" in streamed_data
    assert "logs" in streamed_data


@patch("api.api.SessionStore.get_progress", new_callable=AsyncMock)
def test_download_json_no_session(mock_get):
    """Verifies 404 response on non-existent session cookie identifiers."""
    mock_get.return_value = None

    response = client.get("/json", cookies={"app_state_tracker": "empty-id"})
    assert response.status_code == 404
