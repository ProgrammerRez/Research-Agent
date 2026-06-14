

# Autonomous AI Research Agent Platform

An enterprise-grade, distributed multi-agent research platform designed to automate deep information harvesting, synthesis, and report generation. Powered by LangGraph, FastAPI, Streamlit, and Redis, this system breaks down open-ended research objectives into structured planning execution loops, executing high-concurrency web searches and distilling unstructured data into authoritative production-ready briefs.

---

## 🏗️ System Architecture & Design

The platform shifts away from linear, brittle LLM prompting chains into an **event-driven, state-machine graph topology**. By mapping out agent behaviors as discrete nodes with transactional checkpoint states, the system maintains total fault tolerance across complex, multi-step search networks.

text
```
   [ Streamlit Client UI ] (Port 8501)
             │
             ▼ (HTTP REST via httpx)
   [ FastAPI Gateway App ] (Port 8000) ◄───► [ Redis Cache Store ] (Port 6379)
             │
             ▼ (State Chart Invocations)

```

┌─────────────────────────────────────────────────────────┐
│              LangGraph Workflow Engine                  │
│                                                         │
│    ┌───────────┐       ┌────────────┐       ┌─────────┐ │
│ ──►│ Plan Node │ ─────►│ Fetch Node │ ─────►│ Review  │ │
│    └─────▲─────┘       └─────┬──────┘       └───┬─────┘ │
│          │                   │                  │       │
│          └───────────────────┴──────────────────┘       │
└─────────────────────────────────────────────────────────┘

```



### Core Architecture Breakdown:
1. **The State Fabric (`schema/`)**: An isolated, immutable Pydantic layout mapping out `ResearchState` structures. This enforces absolute runtime schema uniformity across both input/output payload operations.
2. **The Execution Graph (`nodes/`)**: Decoupled, single-responsibility operational components. Each individual node consumes the current active state, executes highly contextual processing operations (e.g., query generation, concurrent raw text extraction, or recursive self-correction), and emits functional state deltas.
3. **The Prompt Vault (`prompts/`)**: Contextually isolated systemic orchestration blueprints mapping instructions to underlying language models, fully separating code logic from prompt configurations.
4. **The Gateway Layer (`api/` / `run_api.py`)**: An asynchronous, horizontally scalable FastAPI interface managing long-running agent threads with structured data verification parameters.
5. **The Memory Controller (`Redis`)**: Captures state checkpoints across every graph step transaction, ensuring seamless historical auditing and resilience against network dropouts.

---

## 📁 Repository Directory Structure

```text
.
├── api/                  # FastAPI Application Layer
│   └── api.py            # Route mappings, application controllers, and endpoint logic
├── app.py                # Streamlit UI Interface (Front-end Chat Canvas)
├── Dockerfile.api        # Isolated image specification for the FastAPI application layer
├── Dockerfile.ui         # Isolated image specification for the Streamlit web layout
├── docker-compose.yml    # Microservice mesh orchestrator manifest
├── main.py               # Central LangGraph initialization, node compilation, and edge wiring
├── Makefile              # Unified automation command hub
├── nodes/                # Python package containing distinct execution graph behaviors
│   ├── __init__.py       # Package markers exposing node operations
│   ├── gather.py         # Concurrent scraping and web information harvesting logic
│   └── summarize.py      # Abstractive condensation and document processing routines
├── prompts/              # Centralized environment prompt mapping configurations
├── run_api.py            # Root runner script adjusting sys.path context boundaries
├── schema/               # Shared Pydantic data modeling structural package
│   └── __init__.py       # Explicit multi-service state data layer layout
└── tests/                # System test harness (Dynamically mounted during development)

```

---

## ⚡ Quickstart: Local Environment Setup

### Prerequisites

* Linux / macOS engine configuration
* Modern Docker daemon engine with `docker-compose` capabilities
* Active Api tokens for **Groq** and **Tavily**

### 1. Establish Secret Variables

Create an active infrastructure configuration environment manifest file named `.env` at your project root:

```ini
# Core Routing Configuration
REDIS_URL=redis://cache:6379
BACKEND_URL=http://api:8000

# Cloud Token Pipeline Provisioning
TAVILY_API_KEY=tvly-your_actual_tavily_token_here
GROQ_API_KEY=gsk_your_actual_groq_token_here

```

### 2. Operational Automation (The Makefile Interface)

The entire deployment, scaling, verification, and testing engine is driven by native operations inside the project `Makefile`.

* **Compile Services**: Build optimized runtime containers and lock down dependencies:
```bash
make build

```


* **Boot Environment**: Spin up the microservice topology securely in the background:
```bash
make up

```


* **Stream Logs**: Monitor transaction cycles, network calls, and agent internal metrics:
```bash
make logs

```


* **Verify Health Check Status**: Ensure internal network layers are operating correctly:
```bash
make status

```



---

## 🧪 Comprehensive Verification & Testing

The platform differentiates between core application code and development verification scripts. To preserve production image boundaries, the `tests/` directory is dynamically mounted into the runtime space at boot time rather than baked statically into the underlying Docker image layers.

### Run Tests Inside the Container Mesh

To evaluate system components using the exact dependencies, configurations, and network isolation configurations mapped within the active Docker deployment infrastructure, run:

```bash
make test

```

*Under the hood:* This bypasses local machine environment variations by triggering `pytest` directly inside the running `research_api_gateway` environment node container.

### Run Tests Locally

If you are developing or modifying schemas inside a local Anaconda/Virtualenv context without invoking container layers, execute:

```bash
make test-local

```

---

## 🛑 Teardown & Maintenance

* **Stop Execution Layers**: Safely bring down the containers while preserving long-term data caches inside the Redis persistent state volume map:
```bash
make down

```


* **Complete System Purge**: Wipe out active container blocks, remove isolated internal bridge networks, drop local storage volumes, and clear cache files entirely:
```bash
make clean

```


* **Hot-Reload Code Alterations**: To push systemic prompt structural upgrades or deep backend file modifications directly into the application space:
```bash
make restart

```



---

## 🔗 Interface Endpoints

Once `make up` confirms active execution states across all services:

* **Interactive Chat Canvas UI**: `http://localhost:8501`
* **FastAPI Core Gateway Engine Docs (Swagger UI)**: `http://localhost:8000/docs`
* **Isolated Redis Network Target Node**: `localhost:6379`
"""

with open("README.md", "w") as f:
f.write(readme_content.strip())

print("README.md successfully written!")

```
Your production-grade `README.md` documentation file is ready. 
[file-tag: code-generated-file-0-1781433424959660054]

This file has been generated at the root of your project directory workspace. It strips out all conversational noise, providing an clean, professional documentation layout. It covers the microservice system architecture design, your precise folder tree footprint, environment variables, execution instructions via the automated `Makefile`, and the system test harness mounting theory.

### Summary of Documentation Principles Applied:
1. **System Design Clarity:** Explicitly diagrams the request-response lifecycle and internal loop execution mapping between Streamlit, FastAPI, Redis, and LangGraph.
2. **Directory Mapping:** Formats the complete physical layout of your codebase (`schema/`, `nodes/`, `prompts/`, etc.) so anyone auditing the repository understands the single-responsibility separation of concerns.
3. **Operations & Maintenance:** Clearly isolates development-stage behavior (the live volume-mounted `tests/` path with `make test`) from immutable production container code logic.

```