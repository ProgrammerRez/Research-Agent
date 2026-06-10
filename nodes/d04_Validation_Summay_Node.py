"""
d04_Validation_Summary.py

The Validation Criteria should be the following:

1. Checks working url -- inefficent
2. Checks for content score -- good
3. Sanitization and taking some number of characters and summarizes them and then loads that summary as a reference file -- getting there
4. Cites the citations as well -- Noice
"""

from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from schema import ResearchState
from dotenv import load_dotenv
import httpx
import asyncio
import re
import os


load_dotenv()


parser = StrOutputParser()
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are an expert technical writer. Convert the provided sanitized text "
                "into structured, production-ready markdown with headers, bullet points, "
                "and code blocks where appropriate. Do not include introductory text."
            ),
        ),
        ("user", "Sanitized Text:\n{text}"),
    ]
)


llm = prompt | ChatGroq(model=os.environ["DEFAULT_MODEL"]) | parser


async def verify_url(url: str, timeout: int = 5):

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
            else:
                return False, f"Broken (Status: {response.status_code})"

        except httpx.UnsupportedProtocol:
            return False, "Error: Invalid URL format (missing http:// or https://)"

        except httpx.ConnectError:
            return (
                False,
                "Error: Failed to connect to the server (Domain may not exist)",
            )

        except httpx.TimeoutException:
            return False, "Error: Request timed out"

        except httpx.RequestError as e:
            return False, f"Error: An unexpected issue occurred ({e})"

        except Exception as e:
            return False, f"Error: An unexpected issue occurred ({e})"


async def validate_score(score: float):
    if score <= float(os.environ["MIN_VAL_SCORE"]):
        return False
    return True


async def sanitize_and_markdownify_text(text: str):

    # 1. Sanitizing Using Regex

    content = re.sub(r"\s+", " ", re.sub(r"[^\w\s\.,!?\-\(\)\[\]]", "", text)).strip()

    # 2. Markdownifying Text

    response = await llm.ainvoke(input={"text": content})

    return response


async def validation_node(state: ResearchState) -> ResearchState:

    all_results = state["results_collected"].items()

    for subtopic, data in all_results:
        results_list = data.get("results", [])

        urls = []
        scores = []
        # content = []

        for item in results_list:
            # 1. Checks Url authenticity
            urls.append(verify_url(item["url"]))
            scores.append(validate_score(item["score"]))

        url_results = await asyncio.gather(*urls)
        scores_results = await asyncio.gather(*scores)

        # Filter and build a clean list of only valid items
        valid_results = []

        for idx, item in enumerate(results_list):
            is_url_valid = url_results[idx][
                0
            ]  # Extracts boolean from (True/False, "msg")
            is_score_valid = scores_results[idx]

            # Keep item only if BOTH validations pass
            if is_url_valid and is_score_valid:
                valid_results.append(item)

        # print(valid_results)

        # 3. Sanitizing Text and converting to markdown with each subtopic being a sub-heading

        all_content = "".join(
            [f"{item['title']} {item['content'][:1000]}" for item in valid_results]
        )

        if all_content:
            final_content = await sanitize_and_markdownify_text(all_content)
            print(final_content)
            state["final_research"] = final_content

        # Update the state directly for this specific subtopic
        state["results_collected"][subtopic]["results"] = valid_results

    # 4. End Citations in at the end of the text

    return state
