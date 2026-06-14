"""
tests/test_schema.py

This file configures pytest and provides a reusable, mock
state template representing a complete session payload from
the redis store
"""

import pytest


@pytest.fixture
def mock_session_payload():
    """Returns a realistic, multi-run mock state payload stored in Redis."""
    return {
        "responses": {
            "2026-06-12T10:00:00": {
                "topic": "Machine Learning Systems Design",
                "research_mode": "ultra-fast",
                "subtopics": ["Architectural Foundations"],
                "results_collected": {},
                "final_research": "# Run 1\nFoundations of system engineering layout.",
            },
            "2026-06-12T11:00:00": {
                "topic": "Machine Learning Systems Design",
                "research_mode": "ultra-fast",
                "subtopics": ["Scalability"],
                "results_collected": {},
                "final_research": "# Run 2\nHorizontal and vertical scaling.",
            },
        },
        "logs": [
            "Successfully ran workflow for topic: Machine Learning Systems Design at 2026-06-12T10:00:00",
            "Successfully ran workflow for topic: Machine Learning Systems Design at 2026-06-12T11:00:00",
        ],
        "costs": (0.0, 0.0),
    }
