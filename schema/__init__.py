from pydantic import BaseModel
from typing import Any, Literal, List, Dict, TypedDict, Optional


class Subtopic_Plan_Node(BaseModel):
    subtopic: List[str]


# The core state for the whole process
class ResearchState(TypedDict):
    # User entered info
    topic: str
    research_mode: Literal["basic", "advanced", "fast", "ultra-fast"]

    # Dynamic Internal Variables
    subtopics: Any
    results_collected: Dict[str, Any] # Maybe include Arxiv and wikipedia but for now we're just going with tavily

    # Final Output Variables:

    final_research: Optional[str]
    summary: Optional[str]
