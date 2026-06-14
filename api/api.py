"""
Research Agent API Gateway
=========================================
A high-performance, stateless FastAPI service that wraps an agentic web-research
graph workflow. This service manages session states across multi-turn user
interactions using an asynchronous Redis backend and HttpOnly tracking cookies.

System Architecture & State Flow
--------------------------------
1. Client sends a request to `/research` with a query topic.
2. The API evaluates or initializes a unique `app_state_tracker` session UUID.
3. The query is passed down to the state graph workflow engine (`main.py`).
4. On success, the raw agent response is merged into a structured session checkpoint
   dictionary, along with incremental system audit logs, and saved to Redis.
5. Tracking identifiers are mirrored back to the client as an HttpOnly cookie.
6. Downstream file compilation routes (`/json`, `/logs`, `/file`) pull directly
   from the Redis state space using this cookie value to dynamically stream assets.

Database Topology (Redis)
-------------------------
- **Key Namespace**: `session:{uuid}`
- **TTL Duration**: 86,400 seconds (24-hour rolling slide per mutation)
- **Schema Mapping**:
    {
        "responses": {
            "ISO-8601-TIMESTAMP": { ...ResearchState Pydantic Layout... }
        },
        "logs": [
            "[ISO-8601] Action / Event log tracking string entry"
        ],
        "costs": [float, float]
    }

API Endpoints Summary
---------------------
* POST `/research` : Receives payload state parameters, awaits agent loop orchestration,
                    commits execution markers to telemetry, and returns raw findings.
* GET  `/json`     : Asynchronously fetches, stringifies, and streams back the complete
                    historical database checkpoint tracking tree as a .json asset.
* GET  `/logs`     : Extracts chronological tracking arrays from memory, joins them
                    via newlines, and streams an atomic plain-text (.txt) audit log.
* GET  `/file`     : Iterates through stored states sequentially by timestamp keys,
                    unwraps the markdown records, appends layout dividers, and streams
                    a consolidated research report (.md).

Dependencies & Lifecycle
-------------------------
- **FastAPI** : Web application engine core framework layer.
- **Redis (async)** : In-memory cluster storage mapping layer using ConnectionPools.
- **orjson** : Blazing fast serialization/deserialization to mitigate latency
                      spikes as session history scales up in size.

Usage / Startup:
    $ python api/api.py
    Or invoke via Uvicorn hot-reload loop:
    $ uvicorn api:app --reload --port 8000
"""

import os
import uuid
import io
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

import uvicorn as uv
import orjson
from fastapi import FastAPI, Request, HTTPException, Response, Depends, Cookie
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis, ConnectionPool

# Import original modules safely
from schema import ResearchState, SessionCheckpoint
from main import main


load_dotenv()


# Initializing an asynchronous connection pool for high-performance sessions for Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
pool = ConnectionPool.from_url(REDIS_URL, decode_responses=False)


def get_redis() -> Redis:
    """Provides a Redis client instance"""
    return Redis(connection_pool=pool)


# Creating a test api for now to test scalability and latency along with api costs
app = FastAPI()

# Session Cookie Setup
SESSION_COOOKIE_NAME = "app_state_tracker"
SESSION_TTL = 86400  # Session expiration time in seconds (24 hours)


# Creating Custom Object for Type-safe fetch/save operation
class SessionStore:
    @staticmethod
    async def get_progress(redis: Redis, session_id: Optional[str]) -> Optional[dict]:
        """Returns the saved session object
            Uses orjson for high-speed
            parsing as the session object grows.

        Args:
            redis (Redis): Asynchronous redis store instance
            session_id (str): session id for state storage in redis

        Returns:
            Optional[dict]: Store Output
        """
        # Verifies whether session_id is provided
        if not session_id:
            return None

        # Fetches and Verifies if data exists
        raw_data = await redis.get(f"session:{session_id}")
        if not raw_data:
            return None

        # Returns orjson object
        return orjson.loads(raw_data)

    @staticmethod
    async def save_progress(redis: Redis, session_id: str, data: dict) -> None:
        """Saves the whole session object in bulk.
            Automatically updates the sliding expiration TTL.

        Args:
            redis (Redis): Asynchronous redis store instance
            session_id (str): session id for state storage in redis
            data (dict): Data collected during the session

        Returns:
            None
        """
        serialized_data = orjson.dumps(data).decode("utf-8")
        await redis.setex(f"session:{session_id}", SESSION_TTL, serialized_data)


# 1. /research endpoint running the workflow
@app.post("/research")
async def research(
    request: Request,
    state: dict,
    response: Response,
    app_state_tracker: Optional[str] = Cookie(default=None),
    redis: Redis = Depends(get_redis),
):
    """
    Runs the main research workflow and stores it in the current running session.
    """
    # 1. Ensure session id exists for the client
    if not app_state_tracker:
        app_state_tracker = str(uuid.uuid4())
        # Set HttpOnly flag for cross-site scripting security
        response.set_cookie(
            key=SESSION_COOOKIE_NAME, value=app_state_tracker, httponly=True
        )

    try:
        # 1. Awaiting for the workflow execution response
        workflow_output = await main(state)  # type: ignore

        # 2. Checking for existing session checkpoint
        existing_checkpoint = await SessionStore.get_progress(redis, app_state_tracker)

        # Initializing a dict with similar structure to session checkpoint
        if not existing_checkpoint:
            existing_checkpoint = {"responses": {}, "logs": [], "costs": [0.0, 0.0]}

        # 3. Generating an ISO format based timestamp
        timestamp_key = datetime.now().isoformat()

        # 4. Adding response to current session
        validated_state = ResearchState(**workflow_output)

        # Check if model_dump exists (Pydantic v2) or fallback to dict() (Pydantic v1)
        if hasattr(validated_state, "model_dump"):
            existing_checkpoint["responses"][timestamp_key] = (
                validated_state.model_dump()
            )
        else:
            existing_checkpoint["responses"][timestamp_key] = validated_state  # type: ignore

        # 5. Maintain audit tracking by logging the execution event
        existing_checkpoint["logs"].append(
            f"[{timestamp_key}] Successfully ran workflow for topic: '{state.get('topic')}' (Mode: {state.get('research_mode')})"
        )
        await SessionStore.save_progress(
            redis=redis, session_id=app_state_tracker, data=existing_checkpoint
        )

    except ConnectionError:
        print("Connection Timeout")
        return state
    except Exception as e:
        print(f"An unexpected error has occured: {e}")
        return state

    return workflow_output


# 2. /json return value will return json file
@app.get("/json")
async def download_json_file(
    app_state_tracker: Optional[str] = Cookie(default=None),
    redis: Redis = Depends(get_redis),
) -> StreamingResponse:
    """Returns a list of objects that have been generated throughout the session"""
    whole_object = await SessionStore.get_progress(redis, app_state_tracker)

    if not whole_object:
        raise HTTPException(status_code=404, detail="No session data found")

    # Log this action to session logs
    timestamp = datetime.now().isoformat()
    whole_object["logs"].append(
        f"[{timestamp}] Session data checkpoint exported via /json"
    )
    await SessionStore.save_progress(redis, app_state_tracker, whole_object)

    # Generate dynamic timestamped filename
    filename = f"current_session_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    serialized_bytes = orjson.dumps(whole_object)

    return StreamingResponse(
        content=io.BytesIO(serialized_bytes),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# 3. /logs will show logs
@app.get("/logs")
async def get_logs(
    app_state_tracker: Optional[str] = Cookie(default=None),
    redis: Redis = Depends(get_redis),
) -> StreamingResponse:
    """Returns a standard txt file with all the logs setup with their time."""
    whole_object = await SessionStore.get_progress(redis, app_state_tracker)

    if not whole_object:
        raise HTTPException(status_code=404, detail="No session data found")

    # Add the log for accessing the log file before compiling
    timestamp = datetime.now().isoformat()
    whole_object["logs"].append(f"[{timestamp}] System audit logs exported via /logs")
    await SessionStore.save_progress(redis, app_state_tracker, whole_object)

    # Combine all historical logs together via raw newlines
    combined_logs = "\n".join(whole_object["logs"])
    filename = f"current_session_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    # FIX: Encoded directly as utf-8 bytes to ensure correct linebreaks in .txt files
    return StreamingResponse(
        content=io.BytesIO(combined_logs.encode("utf-8")),
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# 4. /file returns markdown of research
@app.get("/file")
async def get_file(
    app_state_tracker: Optional[str] = Cookie(default=None),
    redis: Redis = Depends(get_redis),
) -> StreamingResponse:
    """
    Extracts the compiled markdown content from the session,
    sorts by execution timestamp, and returns a downloadable .md file.
    """
    whole_object = await SessionStore.get_progress(redis, app_state_tracker)

    if not whole_object or "responses" not in whole_object:
        raise HTTPException(status_code=404, detail="No session data found")

    responses = whole_object["responses"]
    if not responses:
        raise HTTPException(status_code=404, detail="Session responses are empty")

    # Sort timestamps chronologically to handle out-of-order execution history
    sorted_timestamps = sorted(responses.keys())

    # Extract and combine the raw markdown strings directly
    markdown_contents = []
    for timestamp in sorted_timestamps:
        state_data = responses[timestamp]
        raw_markdown = state_data.get("final_research", "")
        if raw_markdown:
            markdown_contents.append(raw_markdown)

    if not markdown_contents:
        raise HTTPException(
            status_code=404, detail="No markdown text found in session content"
        )

    # Join multiple runs together with clean structural markdown divider bars
    final_file_output = "\n\n---\n\n".join(markdown_contents)

    # Log this file compilation action to session logs
    action_timestamp = datetime.now().isoformat()
    whole_object["logs"].append(
        f"[{action_timestamp}] Consolidated markdown report compiled and downloaded via /file"
    )
    await SessionStore.save_progress(redis, app_state_tracker, whole_object)

    # Generate dynamic timestamped filename
    file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"research_report_{file_timestamp}.md"

    return StreamingResponse(
        content=io.BytesIO(final_file_output.encode("utf-8")),
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


if __name__ == "__main__":
    uv.run(app="api:app", host="0.0.0.0", port=8000, reload=True)
