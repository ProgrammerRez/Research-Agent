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
    async def get_progress(
        redis: Redis, session_id: Optional[str]
    ) -> Optional[dict | SessionCheckpoint]:
        """Returns the saved session object
            Uses orjson [1.4] for high-speed
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
    For further operations

    Args:
        state (dict): A dictionary containing topic and research_mode

    Returns:
        ResearchState: Custom Output Object
    """

    # 1. Ensure session id exists for the client

    if not app_state_tracker:
        app_state_tracker = str(uuid.uuid4())
        # Set HttpOnly flag for cross-site scripting security
        response.set_cookie(
            key=SESSION_COOOKIE_NAME, value=app_state_tracker, httponly=True
        )

    try:
        # 1. Awaiting for the response (FIX: Renamed to avoid overwriting FastAPI response)
        workflow_output = await main(state)  # type: ignore

        # 2. Checking for existing session checkpoint (FIX: Added missing await keyword)
        existing_checkpoint = await SessionStore.get_progress(redis, app_state_tracker)

        # Initializing a dict with similar strcuture to session checkpoint
        if not existing_checkpoint:
            existing_checkpoint = {"responses": {}, "logs": [], "costs": (0.0, 0.0)}

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
            f"Successfully ran workflow for topic: {state.get('topic')} at {timestamp_key}"
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
    """Returns the a list of objects that have been generated throughout the session

    Args:
        app_state_tracker (Optional[str], optional): _description_. Defaults to Cookie(default=None).
        redis (Redis, optional): _description_. Defaults to Depends(get_redis).

    Raises:
        HTTPException: _description_

    Returns:
        StreamingResponse: _description_
    """

    # 1. Fetches the Object being Saved
    whole_object = await SessionStore.get_progress(redis, app_state_tracker)

    # 2. Checking for Null Object
    if not whole_object:
        raise HTTPException(status_code=404, detail="No session data found")

    # 3. Having a filename (**FIX**: Need to put datetime in the name)
    filename = f"current_session_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # 4. Stream the data sequentially to accommodate an infinitely growing payload
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
    """Returns a standard txt file with all the logs setup with their time.

    Args:
        app_state_tracker (Optional[str], optional): _description_. Defaults to Cookie(default=None).
        redis (Redis, optional): _description_. Defaults to Depends(get_redis).

    Returns:
        StreamingResponse: _description_
    """

    # 1. Fetch the Whole Object
    whole_object = await SessionStore.get_progress(redis, app_state_tracker)

    # 2. Check for Null Object
    if not whole_object:
        raise HTTPException(status_code=404, detail="No session data found")

    # 3. Combining all logs:

    combined_logs = "\n".join(whole_object["logs"])

    # 4. Having a filename (**FIX**: Need to put datetime in the name)
    filename = f"current_session_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    # 5. Stream the data sequentially to accommodate an infinitely growing payload
    serialized_bytes = orjson.dumps(combined_logs)

    return StreamingResponse(
        content=io.BytesIO(serialized_bytes),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# 4. /file returns markdown of research
@app.get("/file")
async def get_file(
    app_state_tracker: Optional[str] = Cookie(default=None),
    redis: Redis = Depends(get_redis),
) -> StreamingResponse:
    """Returns the research condcuted as a markdown file

    Args:
        app_state_tracker (Optional[str], optional): _description_. Defaults to Cookie(default=None).
        redis (Redis, optional): _description_. Defaults to Depends(get_redis).

    Returns:
        StreamingResponse: _description_
    """

    # 1. Fetch the Whole Object
    whole_object = SessionStore.get_progress(redis, app_state_tracker)

    #2. Check for Null
    if not whole_object:
        raise HTTPException(status_code=404, detail="No session data found")
    
    # 3. Gathering Research Content
    file_content = whole_object['responses'].items()


# 5. /costs returns current sessions costs


if __name__ == "__main__":
    uv.run(app=app)
