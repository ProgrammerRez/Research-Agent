"""
d04_Validation_Summary.py

The Validation Criteria should be the following:

1. Checks working url -- inefficent
2. Checks for content score -- good
3. Sanitization and taking some number of characters and summarizes them and then loads that summary as a reference file -- getting there
4. Cites the citations as well -- Noice
"""

from langchain_groq import ChatGroq
from schema import ResearchState
from dotenv import load_dotenv
import requests
import json


async def validation_node(state: ResearchState) -> ResearchState:

    # 1. Checks Url authenticity

    # 2. Content Score Check --- .env based or dynamic (based on len(results and subtopics))

    # 3. Sanitizing Text and converting to markdown with each subtopic being a sub-heading

    # 4. End Citations in at the end of the text

    return state
