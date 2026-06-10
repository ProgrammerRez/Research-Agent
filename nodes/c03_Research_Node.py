"""
node/c03_Research_Node.py

Concurrent Research Processing Node for Tavily Search Pipelines.

The Node Logic covers:
1. Dynamic Result Sizing: Adjusts search depth bounds automatically based on the number of subtopics.
2. Hard Credit Capping: Truncates incoming topics to safely defend account budget billing constraints.
3. Asynchronous Execution: Executes all external queries concurrently using asyncio.gather tasks.
4. Clean JSON Serialization: Maps structural data properties into an interoperable payload structure.
"""

from schema import ResearchState
from tavily import AsyncTavilyClient
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()

# Global API Client Singleton to manage connection pooling efficiently across executions
tav = AsyncTavilyClient()


async def research_node(state: ResearchState) -> ResearchState:
    """
    Executes deep or basic web search requests for all assigned subtopics concurrently.

    Dynamically balances payload volume, enforces strict safety boundaries to manage credit costs,
    handles runtime connection errors gracefully per search phrase, and compiles raw
    responses into structured dictionary formats within the shared context state.

    Args:
        state (ResearchState): The state memory tracker passed down by the LangGraph runner.

    Returns:
        ResearchState: The updated global state containing structured text results per subtopic.
    """
    subtopics = state.get("subtopics", [])
    if not subtopics:
        print("no subtopics")
        return state

    num_topics = len(subtopics)

    # Optimization 1: Determining Search Results population bounds based on subtopic counts
    if num_topics <= 2:
        max_results = int(os.getenv("TAVILY_MAX_RESULTS_MAX", 5))
    elif num_topics <= 5:
        max_results = int(os.getenv("TAVILY_MAX_RESULTS_MED", 3))
    else:
        max_results = int(os.getenv("TAVILY_MAX_RESULTS_MIN", 1))

    # Optimization 3: Hard Credit Caps / Rate Limiting configuration bounds protection
    CREDIT_CAP = int(os.getenv("TAVILY_NODE_CREDIT_CAP", 10))
    if num_topics > CREDIT_CAP:
        subtopics = subtopics[:CREDIT_CAP]

    # Initialize concurrent operational tracking tasks
    tasks = [
        tav.search(
            query=topic,
            max_results=max_results,
            search_depth=state.get("research_mode", "basic"),
        )
        for topic in subtopics
    ]

    # Execute all background network search requests simultaneously
    search_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Optimization 2: Formatting output collections into highly readable target structures
    clean_results = {}
    for topic, result in zip(subtopics, search_results):
        if isinstance(result, Exception):
            clean_results[topic] = {"error": str(result), "results": []}
        else:
            clean_results[topic] = {
                "query": result.get("query"),
                "answer": result.get("answer", ""),
                "results": [
                    {
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "content": item.get("content"),
                        "score": item.get("score"),
                    }
                    for item in result.get("results", [])
                ],
            }

    state["results_collected"] = clean_results
    return state
