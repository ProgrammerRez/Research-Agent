from pydantic import BaseModel, Field
from typing import Any, Literal, List, Dict


class Subtopic_Plan_Node(BaseModel):
    subtopic : List[str] 

# The core state for the whole process
class ResearchState(BaseModel):
    
    # User entered info
    topic: str = ''
    research_mode: Literal["shallow", "deep"] = 'shallow'
    
    # Dynamic Internal Variables
    
    subtopics: Any = []
    results_collected: Dict[str, Any] = Field(default_factory=dict)  # Maybe include Arxiv and wikipedia but for now we're just going with tavily
    
    # Final Output Variables:
    
    final_research: Dict[str, Any] = Field(default_factory=dict)
    summary: str = """"""
