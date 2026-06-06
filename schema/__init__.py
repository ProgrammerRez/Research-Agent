from pydantic import BaseModel, Field
from typing import Optional, Any, Literal, List


# The core state for the whole process
class ResearchState(BaseModel):
    
    # User entered info
    topic: str = ''
    research_mode: Literal["shallow", "deep"] = 'shallow'
    
    # Dynamic Internal Variables
    
    subtopics: List[str] = []
    results_collected: List[Any] = [] # Maybe include Arxiv and wikipedia but for now we're just going with tavily
    
    # Final Output Variables:
    
    final_research: List[Any] = []
    summary: str = """"""
