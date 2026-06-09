"""
node/b02_Planning_Node.py

This node analyzes the topic and based on the research mode decides
how and what subtopics to include for the research.
"""

from schema import ResearchState, Subtopic_Plan_Node
from prompts import DEEP_RESEARCH_PROMPT, SHALLOW_RESEARCH_PROMPT
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os


load_dotenv()


async def plan_node(state: ResearchState) -> ResearchState:
    """
    This node first declares an LLM instance with
    specialized output schema `Subtopic_Plan_Node` and decides prompt based
    on `deep` or `shallow` `research_mode`, then adds it to the `subtopic`
    attribute in `state`. Then returns `state`.
    """

    # 01. Defining the LLM object
    llm = ChatGroq(model=str(os.environ["DEFAULT_MODEL"])).with_structured_output(
        Subtopic_Plan_Node
    )
    # 02. Deciding Prompt based on Research Mode
    prompt = (
        DEEP_RESEARCH_PROMPT
        if state.research_mode == "deep"
        else SHALLOW_RESEARCH_PROMPT
    )

    # 03. Building and Running Chain
    chain = ChatPromptTemplate.from_messages(prompt) | llm

    result = await chain.ainvoke({"topic": state.topic})  # type: ignore

    # state.subtopics = result if type(result)==List else []
    print(result)
    print(type(result))
    state.subtopics = result
    # 04. Returning State
    return state
