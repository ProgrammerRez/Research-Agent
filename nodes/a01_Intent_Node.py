"""
node/a01_Intent_Node.py

Primarily parses user input and analyzes intent and arranges input.
It functions as more of a debug node.
"""

from schema import ResearchState


async def intent_node(state: ResearchState) -> ResearchState:
    """
    Takes the `topic` and `reserach_mode` attribute and
    arranges and logs them
    """
    return state
