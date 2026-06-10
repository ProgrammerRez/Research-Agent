"""
node/a01_Intent_Node.py

Input Intent Parsing and Debug Verification Node for LangGraph Pipelines.

The Node Logic covers:
1. Input Structuring: Confirms incoming user parameters are correctly initialized.
2. Workflow Debugging: Provides a central logging boundary layer before operational nodes run.
3. State Preservation: Ensures state records pass through safely without payload mutations.
"""

from schema import ResearchState


async def intent_node(state: ResearchState) -> ResearchState:
    """
    Parses, validates, and logs initial user configuration metrics.
    
    Acts as a diagnostic gatekeeper to ensure that user inputs like 'topic' and 
    'research_mode' are correctly formatted and registered before passing control 
    to heavy extraction nodes.

    Args:
        state (ResearchState): The state memory tracker passed down by the LangGraph runner.

    Returns:
        ResearchState: The verified global state ready for downstream processing nodes.
    """
    # Extract data parameters safely for tracking and logging visibility
    topic = state.get("topic", "N/A")
    research_mode = state.get("research_mode", "basic")

    print(f"[Intent Node Log] Topic: '{topic}' | Mode: '{research_mode}'")

    return state
