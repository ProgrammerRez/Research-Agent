"""
node/c03_Research_Node.py

This node loads the subtopics and runs an async group of
tasks that gather a single result for each subtopic.



**Possible Optimization**
1. Max Results should be either in .env or should be dynamic in terms of len(subtopics)
2. results should be stored in a pass down json object
3. Set Credit Caps (if possible)
"""

from schema import ResearchState

# from langchain_tavily import TavilySearch
from tavily import AsyncTavilyClient
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()

tav = AsyncTavilyClient()


async def research_node(state: ResearchState) -> ResearchState:
    """
    Executes searches for all subtopics concurrently and returns the updated state.
    """
    # subtopics = state["subtopics"] if hasattr(state, "subtopics") else []
    subtopics = state.get("subtopics", [])
    # subtopics = ["machine learning research", "artificial intelligence trends 2024"]
    if not subtopics:
        print("no subtopics")
        return state

    # Optimization 1: Determining Search Results population based on number of subtopics
    # Fewer topics = pull deeper records; Too many topics = cap them to prevent payload bloat

    num_topics = len(subtopics)

    if num_topics <= 2:
        max_results = int(os.getenv("TAVILY_MAX_RESULTS_MAX", 5))
    elif num_topics <= 5:
        max_results = int(os.getenv("TAVILY_MAX_RESULTS_MED", 3))
    else:
        max_results = int(os.getenv("TAVILY_MAX_RESULTS_MIN", 1))

    # Optimization 3: Optional Hard Credit Caps / Rate Limiting per node lifecycle
    # Protects account billing if an upstream LLM gets stuck in a loop generating 50 subtopics
    CREDIT_CAP = int(os.getenv("TAVILY_NODE_CREDIT_CAP", 10))
    if num_topics > CREDIT_CAP:
        subtopics = subtopics[
            :CREDIT_CAP
        ]  # Truncate tasks to strictly defend the credit ceiling

    # Create a list of async tasks running concurrently
    tasks = [
        tav.search(
            query=topic,
            max_results=max_results,
            search_depth=state.get("research_mode", "basic"),
        )
        for topic in subtopics
    ]

    # 2. Await all tasks simultaneously
    search_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Optimization 2: Structuring Results as an interoperable JSON Payload
    clean_results = {}
    for topic, result in zip(subtopics, search_results):
        # 1. Checking for excpetions
        if isinstance(result, Exception):
            # Gracefully log the exceptions
            clean_results[topic] = {"error": str(result), "results": []}
        else:
            # Mapping clear and meaningful keys out of the raw response

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
