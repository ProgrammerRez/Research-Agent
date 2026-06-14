import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from api.api import app

# 1. Creating client test object
client = TestClient(app=app)


# 2. Testing Log Extraction Stream Function
@patch("api.api.SessionStore.save_progress", new_callable=AsyncMock)
@patch("api.api.SessionStore.get_progress", new_callable=AsyncMock)
def test_json_download_file_success(mock_get, mock_save, mock_session_payload):
    """Verifies the raw dictionary state is accurately serialized and streamed."""
    mock_get.return_value = mock_session_payload
    mock_save.return_value = True

    response = client.get("/json", cookies={"app_state_tracker": "session_id_123"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment; filename=" in response.headers["content-disposition"]


@patch("api.api.SessionStore.get_progress", new_callable=AsyncMock)
def test_download_json_no_session(mock_get):
    """Verifies 404 response on non-existent session cookie identifiers."""
    mock_get.return_value = None

    response = client.get("/json", cookies={"app_state_tracker": "empty-id"})
    assert response.status_code == 404