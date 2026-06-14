import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from api.api import app

# 1. Creating Client Test Object for fastapi app
client = TestClient(app)


# 2. Corrected dot notation paths on all patch decorators
@patch("api.api.main", new_callable=AsyncMock)
@patch("api.api.SessionStore.get_progress", new_callable=AsyncMock)
@patch("api.api.SessionStore.save_progress", new_callable=AsyncMock)
def test_research(mock_save, mock_get, mock_main_workflow):
    """Verifies workflow execution, cookie creation, and checkpoint merging."""

    mock_main_workflow.return_value = {
        "topic": "Distributed Storage",
        "research_mode": "ultra-fast",
        "subtopics": ["Sharding"],
        "results_collected": {},
        "final_research": "Raw markdown string text output",
    }

    mock_get.return_value = None  # Simulates a brand new session initialization

    # 3. FIX: Fixed case-sensitivity typo ("DIstributed" -> "Distributed")
    payload = {"topic": "Distributed Storage", "research_mode": "fast"}
    response = client.post("/research", json=payload)

    # 4. Assertions
    assert response.status_code == 200
    assert response.json()["topic"] == "Distributed Storage"

    # 5. Assert Cookie is there
    assert "app_state_tracker" in response.cookies

    # 6. Verify persistence pipeline was hit
    assert mock_main_workflow.called
    assert mock_save.called


# FIX: Corrected target string lookup path from 'api_module.main' to 'api.api.main'
@patch("api.api.main", new_callable=AsyncMock)
def test_research_endpoint_handling(mock_main_workflow):
    """Ensures app returns the original input state safely if an internal crash happens."""
    
    mock_main_workflow.side_effect = Exception("Agent runtime execution failed")
    
    payload = {"topic": "Broken Workflow", "research_mode": "fast"}
    response = client.post("/research", json=payload)
    
    assert response.status_code == 200
    assert response.json() == payload