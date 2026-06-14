"""
Enterprise Research Agent Workspace UI
======================================
A stateful, reactive Streamlit web interface designed as a chatbot workspace.
This application communicates asynchronously with a decoupled FastAPI gateway
to trigger intensive research loops, while executing secondary conversational
follow-ups locally via the LangChain Groq integration ecosystem.

Frontend State Management
-------------------------
Streamlit re-executes scripts from top to bottom on every user interaction.
To maintain a persistent user workspace, this script handles state via:
1. `st.session_state["app_state_tracker"]`: Captures and stores the unique Redis
   UUID session cookie returned by FastAPI to maintain sticky session states.
2. `st.session_state["chat_history"]`: Holds the current UI message stream array
   to keep the chat dialogue rendering properly across UI updates.
3. `st.session_state["base_research_context"]`: Caches the raw markdown report string.
   When empty, incoming queries run web research via API. When populated, queries
   switch to local conversational inference mode.

Dual-Phase Execution Loop
-------------------------
- **Phase 1 (Deep-Dive Research)**: Occurs when no prior context exists. The user
  submits a query, and the script issues a blocking POST request to the backend's
  `/research` route to perform a heavy web-scraping cycle.
- **Phase 2 (Contextual Chat)**: Triggered automatically once a report lands in memory.
  Follow-up prompts bypass the backend entirely. They initialize a `ChatGroq` LLM
  and pass conversation histories through a structured `ChatPromptTemplate` acting
  as an on-the-fly context injection framework.

UI Component Layout
-------------------
- **Sidebar**: Controls API keys hydration, sets the workflow engine execution mode,
  and provides an intuitive download center for file components.
- **Main Canvas**: A chat stream container that dynamically switches from a loading
  spinner to a rendered markdown layout.

Usage / Startup:
    $ streamlit run app.py
"""

import os
import httpx
import streamlit as st
from dotenv import load_dotenv

# LangChain Structural Core Components
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# 1. SETUP PAGE CONFIG FIRST (Mandatory Streamlit lifecycle execution rule)
st.set_page_config(
    page_title="Enterprise grade research agent",
    initial_sidebar_state="expanded",
    layout="wide",
)

load_dotenv(".env")

# Network Target Setup
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Initialize UI Memory Keys
if "app_state_tracker" not in st.session_state:
    st.session_state["app_state_tracker"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "base_research_context" not in st.session_state:
    st.session_state["base_research_context"] = None

# Creating Page Title
st.title("Enterprise Grade Research Agent Preview")

# Setting a divider
st.divider()

# Creating the Sidebar
with st.sidebar:
    st.title("Control Panel")
    st.divider()
    st.subheader("Credit / API Keys")

    # Checking for available api keys dynamically
    tavily_env = os.environ.get("TAVILY_API_KEY", "")
    groq_env = os.environ.get("GROQ_API_KEY", "")

    if not (tavily_env and groq_env):
        st.warning("Kindly enter your api keys for a functional experience")
        tavily_input = st.text_input("Tavily API Key", type="password")
        groq_input = st.text_input("Groq API Key", type="password")

        if tavily_input:
            os.environ["TAVILY_API_KEY"] = tavily_input
        if groq_input:
            os.environ["GROQ_API_KEY"] = groq_input
    else:
        st.success("API Credentials Active")

    st.divider()
    st.subheader("Tuning Configuration")
    research_mode = st.select_slider(
        "Research Mode (Decides Speed and Tokens)",
        options=["ultra-fast", "fast", "basic", "advanced"],
    )

    # ==========================================
    # USER-FRIENDLY ONE-CLICK DOWNLOAD CENTER
    # ==========================================
    st.divider()
    st.subheader("Download Artifacts")

    if st.session_state["app_state_tracker"]:
        headers = {
            "Cookie": f"app_state_tracker={st.session_state['app_state_tracker']}"
        }
        st.caption("📥 Download generated workflow assets directly in 1-click:")

        # 1. Direct Markdown Report Download
        try:
            file_res = httpx.get(f"{BACKEND_URL}/file", headers=headers)
            if file_res.status_code == 200:
                st.download_button(
                    label="📄 Download Research Report (.md)",
                    data=file_res.content,
                    file_name="research_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
        except Exception:
            st.error("Failed to connect to report download stream.")

        # 2. Direct Plain-text System Logs Download
        try:
            log_res = httpx.get(f"{BACKEND_URL}/logs", headers=headers)
            if log_res.status_code == 200:
                st.download_button(
                    label="📋 Download Execution Logs (.txt)",
                    data=log_res.content,
                    file_name="session_logs.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
        except Exception:
            pass

        # 3. Direct JSON State Tree Download
        try:
            json_res = httpx.get(f"{BACKEND_URL}/json", headers=headers)
            if json_res.status_code == 200:
                st.download_button(
                    label="⚙️ Download State Snapshot (.json)",
                    data=json_res.content,
                    file_name="session_state.json",
                    mime="application/json",
                    use_container_width=True,
                )
        except Exception:
            pass

    else:
        st.info(
            "💡 Complete an initial research query below to enable artifact downloads."
        )

# ==========================================
# CHATBOT INTERFACE & CONVERSATION SURFACE
# ==========================================

# Render conversation history stream
for msg in st.session_state["chat_history"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Chat Action Entry Point
if prompt := st.chat_input(
    "Enter a new research topic, or chat about your active file..."
):
    # Render user query right away
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state["chat_history"].append({"role": "user", "content": prompt})

    # PHASE 1: BRAND NEW RUN (No historical research file context exists yet)
    if st.session_state["base_research_context"] is None:
        with st.chat_message("assistant"):
            with st.spinner(
                "Initializing Deep Web Research Engine Pipelines via API..."
            ):
                try:
                    headers = {}
                    if st.session_state["app_state_tracker"]:
                        headers["Cookie"] = (
                            f"app_state_tracker={st.session_state['app_state_tracker']}"
                        )

                    payload = {"topic": prompt, "research_mode": research_mode}
                    response = httpx.post(
                        f"{BACKEND_URL}/research",
                        json=payload,
                        headers=headers,
                        timeout=300.0,
                    )

                    if response.status_code == 200:
                        raw_data = response.json()

                        # Catch and stick session cookie reference
                        if "app_state_tracker" in response.cookies:
                            st.session_state["app_state_tracker"] = response.cookies[
                                "app_state_tracker"
                            ]

                        # Handle either raw response or nested object returns safely
                        final_markdown = (
                            raw_data.get("final_research", "")
                            if isinstance(raw_data, dict)
                            else ""
                        )
                        if not final_markdown and "responses" in raw_data:
                            latest_ts = sorted(raw_data["responses"].keys())[-1]
                            final_markdown = raw_data["responses"][latest_ts].get(
                                "final_research", ""
                            )

                        # Commit the generated file text into layout context cache
                        st.session_state["base_research_context"] = final_markdown

                        st.markdown(final_markdown)
                        st.session_state["chat_history"].append(
                            {"role": "assistant", "content": final_markdown}
                        )
                        st.rerun()
                    else:
                        st.error(
                            f"Backend Server Error: HTTP status code {response.status_code}"
                        )
                except Exception as e:
                    st.error(f"Failed to communicate with research backend: {e}")

    # PHASE 2: FOLLOW-UP CHAT MODE (Runs locally using ChatGroq & ChatPromptTemplate)
    else:
        with st.chat_message("assistant"):
            with st.spinner(
                "Analyzing document context state via local LangChain engine..."
            ):
                try:
                    active_groq_key = os.environ.get("GROQ_API_KEY", "")
                    if not active_groq_key:
                        st.error(
                            "Please add a valid GROQ_API_KEY to the sidebar to chat about this document."
                        )
                        st.stop()

                    # 1. Initialize LangChain's ChatGroq class wrapper
                    llm = ChatGroq(
                        api_key=str(active_groq_key),
                        model=os.getenv("STREAMLIT_MODEL", "llama-3.1-8b-instant"),
                        temperature=0.3,
                        max_tokens=2048,
                    )

                    # 2. Compose the structured prompt layout using LangChain's template engine
                    prompt_template = ChatPromptTemplate.from_messages(
                        [
                            (
                                "system",
                                "You are an expert technical advisor. You are answering user questions based strictly "
                                "on the following generated research document:\n\n{context_document}\n\n"
                                "Rely completely on the provided context. If the answer cannot be found in the document, "
                                "politely inform the user that the information falls outside the research scope.",
                            ),
                            MessagesPlaceholder(variable_name="history"),
                        ]
                    )

                    # 3. Transform UI chat history entries into typed LangChain Message objects
                    langchain_message_history = []
                    for h_msg in st.session_state["chat_history"]:
                        if h_msg["role"] == "user":
                            langchain_message_history.append(
                                HumanMessage(content=h_msg["content"])
                            )
                        elif h_msg["role"] == "assistant":
                            langchain_message_history.append(
                                AIMessage(content=h_msg["content"])
                            )

                    # 4. Build execution chain and invoke
                    chain = prompt_template | llm
                    response_object = chain.invoke(
                        {
                            "context_document": st.session_state[
                                "base_research_context"
                            ],
                            "history": langchain_message_history,
                        }
                    )

                    # 5. Extract output string content and display
                    ai_response = response_object.content
                    st.markdown(ai_response)
                    st.session_state["chat_history"].append(
                        {"role": "assistant", "content": ai_response}
                    )
                    st.rerun()

                except Exception as e:
                    st.error(f"LangChain Context Inference Error: {e}")
