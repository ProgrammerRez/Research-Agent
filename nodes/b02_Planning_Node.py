"""
node/b02_Planning_Node.py

Strategic Research Planning Node for LangGraph Generation Workflows.

The Node Logic covers:
1. Shared LLM Instance Management: Reuses a single global baseline ChatGroq client model,
   completely eliminating initialization overhead and cold-start latency.
2. Dynamic Parameter and Token Tracking: Passes configurable parameters like max subtopic
   bounds directly from environment rules to protect downstream API credit cost ceilings.
3. Adaptive Prompt Strategy Routing: Inspects global execution state mode metrics to inject
   either advanced deep-dive templates or fast shallow-sweep instructions dynamically.
4. Structured Schema Parsing: Enforces strict data contract validations at the boundary layer
   using a compiled Subtopic_Plan_Node framework.
"""

from schema import ResearchState, Subtopic_Plan_Node
from prompts import DEEP_RESEARCH_PROMPT, SHALLOW_RESEARCH_PROMPT
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

# --- OPTIMIZATION 3: Global Single Client Instance (Eliminates repeated instantiation costs) ---
_base_llm = ChatGroq(
    model=str(os.environ["DEFAULT_MODEL"]),
    max_tokens=int(os.getenv("MAX_TOKENS", 1000)),
    max_retries=int(os.getenv("MAX_RETRIES", 2))
)

# Compile structured validation schemas early at the module root boundary layer
STRUCTURED_PLAN_LLM = _base_llm.with_structured_output(Subtopic_Plan_Node)


async def plan_node(state: ResearchState) -> ResearchState:
    """
    Analyzes user research queries to map out relevant, high-utility technical subtopics.

    Routes processing tasks based on research track depth, applies strict fallback safety rules,
    and handles state modifications cleanly to safeguard downstream search extraction pools.

    Args:
        state (ResearchState): The state memory tracker passed down by the LangGraph runner.

    Returns:
        ResearchState: The updated global state containing structured list arrays of subtopic titles.
    """
    # --- OPTIMIZATION 2: Dynamic Token and Quantity Controls (Eliminates hardcoded boundaries) ---
    max_allowed_subtopics = int(os.environ.get("MAX_PLANNER_SUBTOPICS", 5))

    # 01. Deciding Prompt layout strategy based on context execution mode settings
    prompt_messages = (
        DEEP_RESEARCH_PROMPT
        if state.get("research_mode") == "advanced"
        else SHALLOW_RESEARCH_PROMPT
    )

    # 02. Building and running transaction compilation chains
    chain = ChatPromptTemplate.from_messages(prompt_messages) | STRUCTURED_PLAN_LLM

    # Pass configuration constraints directly to inform LLM generation limits
    result = await chain.ainvoke(
        {"topic": state.get("topic", ""), "max_subtopics": max_allowed_subtopics}
    )

    # 03. State unpacking and reference extraction
    extracted_subtopics = []
    if result and hasattr(result, "subtopic") and result.subtopic:
        extracted_subtopics = result.subtopic

        # --- OPTIMIZATION 1: Token Protection (Defensively cap list slices against payload bloat) ---
        if len(extracted_subtopics) > max_allowed_subtopics:
            extracted_subtopics = extracted_subtopics[:max_allowed_subtopics]

    print(f"Generated Subtopics: {extracted_subtopics}")

    # Commit changes safely back into the shared state registry
    state["subtopics"] = extracted_subtopics
    return state
