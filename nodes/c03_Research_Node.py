"""
node/c03_Research_Node.py

This node loads the subtopics and runs an async group of
tasks that gather a single result for each subtopic.
"""

from schema import ResearchState
from langchain_tavily import TavilySearch
from dotenv import load_dotenv
import asyncio


load_dotenv()

tav = TavilySearch(max_results=1)


async def research_node(state: ResearchState) -> ResearchState:
    """
    Executes searches for all subtopics concurrently and returns the updated state.
    """
    subtopics = state.subtopics.subtopic
    # subtopics = ["machine learning research", "artificial intelligence trends 2024"]
    if not subtopics:
        return state

    # 1. Create a list of async tasks running concurrently
    tasks = [tav.ainvoke(topic) for topic in subtopics]

    # 2. Await all tasks simultaneously
    search_results = await asyncio.gather(*tasks)

    # 3. Map topics to their corresponding results
    new_results = {topic: result for topic, result in zip(subtopics, search_results)}

    # 4. Return the partial state update (LangGraph merges this automatically)
    state.results_collected = new_results
    return state
