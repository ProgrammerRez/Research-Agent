from pydantic import BaseModel
from typing import Any, Literal, List, Dict, Optional, Tuple
from typing_extensions import TypedDict
from datetime import datetime


class Subtopic_Plan_Node(BaseModel):
    subtopic: List[str]


# The core state for the whole process
class ResearchState(TypedDict):
    # User entered info
    topic: str
    research_mode: Literal["basic", "advanced", "fast", "ultra-fast"]

    # Dynamic Internal Variables
    subtopics: Any
    results_collected: Dict[
        str, Any
    ]  # Maybe include Arxiv and wikipedia but for now we're just going with tavily

    # Final Output Variables:

    final_research: Optional[str]


# The session progress object for api endpoints(/json, /file, /cost, /logs)
class SessionCheckpoint(TypedDict):
    
    # Carries responses with timestamp
    responses: Dict[str, ResearchState]
    
    # Logs for the current session
    logs: List[str]
    
    # Token/ API Costs for the current session
    # First: GROQ API, Second: Tavily API
    costs: Tuple[float, float]
