"""
d04_Validation_Summary.py

Validation and Summarisation Processing Node for LangGraph Research Pipelines.

The Validation Criteria covers:
1. URL Authenticity Validation: Evaluates live HTTP status codes concurrently via HEAD/GET tasks.
2. Content Quality Thresholding: Dynamically filters weak search hits using .env metric boundaries.
3. Strict Token Optimization & Summarisation: Strips unnecessary characters using optimized regular
    expressions, groups all remaining contents, and reduces the prompt overhead down to a single
    bulk ChatGroq LLM invocation.
4. Continuous End-Citations Append: Re-indexes valid nodes and binds uniform references at the
    terminal boundary of the file.
"""

from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from prompts import SANITIZATION_PROMPT
from schema import ResearchState
from dotenv import load_dotenv
import httpx
import asyncio
import re
import os

load_dotenv()

# Global Client Singletons (Prevents cold-start connection and memory overheads across nodes)
_base_llm = ChatGroq(
    model=os.environ["DEFAULT_MODEL"],
    max_tokens=int(os.getenv("MAX_TOKENS", 1000)),
    max_retries=int(os.getenv("MAX_RETRIES", 2)),
)

parser = StrOutputParser()

prompt = ChatPromptTemplate.from_messages(SANITIZATION_PROMPT)

MARKDOWN_LLM = prompt | _base_llm | parser


async def verify_url(url: str, timeout: int = 5) -> tuple[bool, str]:
    """
    Asynchronously checks the connectivity and validity of a given URL.

    Args:
        url (str): The web target address to test.
        timeout (int): The maximum waiting timeframe in seconds before abandoning requests.

    Returns:
        tuple[bool, str]: A validation success flag paired with a descriptive HTTP status message.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    async with httpx.AsyncClient(
        headers=headers, timeout=timeout, follow_redirects=True
    ) as client:
        try:
            response = await client.head(url=url)
            if response.status_code in [404, 405, 501]:
                response = await client.get(url=url)
            if response.is_success or response.is_redirect:
                return True, f"Working (Status: {response.status_code})"
            return False, f"Broken (Status: {response.status_code})"
        except Exception:
            return False, "Error: Connection Failure"


async def validate_score(score: float) -> bool:
    """
    Validates a single source content reliability metric against environment configurations.

    Args:
        score (float): The computational confidence value returned by the search engine.

    Returns:
        bool: True if the source satisfies or surpasses the configured baseline, False otherwise.
    """
    return score >= float(os.environ.get("MIN_VAL_SCORE", 0.50))


async def sanitize_and_markdownify_text(text: str) -> str:
    """
    Applies aggressive regular expressions to normalize characters and calls
    the unified global LLM chain to render valid markdown.

    Args:
        text (str): The concatenated raw title and content source string.

    Returns:
        str: Clean, formatted markdown documentation text blocks block.
    """
    max_tokens_budget = int(os.environ.get("MAX_TEXT_SNIPPET_CHARS", 1500))

    # 1. Regex Cleanup: Strips unexpected text characters and squashes extra whitespace
    content = re.sub(r"\s+", " ", re.sub(r"[^\w\s\.,!?\-\(\)\[\]]", "", text)).strip()
    truncated_content = content[:max_tokens_budget]

    # 2. Markdown Conversion
    response = await MARKDOWN_LLM.ainvoke(input={"text": truncated_content})
    return response


async def validation_node(state: ResearchState) -> ResearchState:
    """
    The main runtime execution engine for data filtering, processing, and reference generation.

    Processes the raw results collected per subtopic, filters dead links or low-confidence nodes
    concurrently, and bundles text payloads into a single Groq transaction to save token costs.

    Args:
        state (ResearchState): The state memory tracker passed down by the LangGraph runner.

    Returns:
        ResearchState: The updated global state containing filtered results and the markdown reference file.
    """

    # 1. Parsing JSON Object for collected_results

    all_results = state["results_collected"].items()
    combined_valid_text_blocks = []
    citation_list = []
    citation_idx = 1

    for subtopic, data in all_results:
        results_list = data.get("results", [])
        if not results_list:
            continue

        # 2. Running URL Verfication and Score Validation
        urls = [verify_url(item["url"]) for item in results_list]
        scores = [validate_score(item["score"]) for item in results_list]

        url_results = await asyncio.gather(*urls)
        scores_results = await asyncio.gather(*scores)

        # 3.Combining them under Valid Results
        valid_results = []
        subtopic_content_accumulator = []

        for idx, item in enumerate(results_list):
            is_url_valid = (
                url_results[idx][0] if isinstance(url_results[idx], tuple) else False
            )
            is_score_valid = scores_results[idx]

            if is_url_valid and is_score_valid:
                valid_results.append(item)

                # 4. Collecting content and titles for text sanitization
                title = item.get("title", "Source Document")
                content_str = item.get("content", "")
                subtopic_content_accumulator.append(
                    f"Source: {title} | Content: {content_str}"
                )

                citation_list.append(f"[{citation_idx}] {title} - {item['url']}")
                citation_idx += 1
        # 5. Combining Text and Sanitizing
        if subtopic_content_accumulator:
            joined_subtopic_text = f"### Subtopic: {subtopic}\n" + " ".join(
                subtopic_content_accumulator
            )
            combined_valid_text_blocks.append(joined_subtopic_text)

        state["results_collected"][subtopic]["results"] = valid_results

    if combined_valid_text_blocks:
        full_document_payload = "\n\n".join(combined_valid_text_blocks)
        final_markdown_report = await sanitize_and_markdownify_text(
            full_document_payload
        )
        # 6. Checking for Citations
        if citation_list:
            final_markdown_report += "\n\n## References & Citations\n" + "\n".join(
                citation_list
            )

        print(final_markdown_report)
        state["final_research"] = final_markdown_report

    return state
