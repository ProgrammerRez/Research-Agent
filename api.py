from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from schema import ResearchState, SessionCheckpoint
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional
from main import main
import uvicorn as uv
import os


load_dotenv()

# Creating a test api for now to test scalability and latency along with api costs
app = FastAPI()

# Adding middleware for session based context/history

app.add_middleware(
    middleware_class=SessionMiddleware,
    secret_key=str(os.getenv("SECRET_KEY", "")),
    session_cookie="app_state_tracker",
)


# Creating Custom Object for Type-safe fetch/save operation
class SessionStore:
    @staticmethod
    def get_progress(request: Request) -> Optional[SessionCheckpoint]:
        """Returns the saved session object

        Args:
            request (Request): Standard Request Object from fastapi library

        Returns:
            Optional[SessionCheckpoint]: Custom object created for session data storage
        """
        return request.session.get("current_state")

    @staticmethod
    def save_progress(request: Request, data: SessionCheckpoint) -> None:
        """Saves the whole session object in bulk.

        Args:
            request (Request): Standard Request Object from fastapi library
            data (SessionCheckpoint): Current Session Data wrapped in a custom object

        Returns:
            None
        """
        request.session["current_state"] = data


# 1. /research endpoint will run the workflow
@app.post("/research")
async def research(request: Request, state: dict):
    """
    Runs the main research workflow and stores it in the current running session.
    For further operations

    Args:
        state (dict): A dictionary containing topic and research_mode

    Returns:
        ResearchState: Custom Output Object
    """

    try:
        # 1. Awaiting for the response
        response = await main(state)  # type: ignore

        # 2. Checking for existing session checkpoint
        existing_checkpoint: SessionCheckpoint = SessionStore.get_progress(request)

        if not existing_checkpoint:
            existing_checkpoint = SessionCheckpoint(
                responses={}, logs=[], costs=(0.0, 0.0)
            )

        # 3. Generating an ISO format based timestamp
        timestamp_key = datetime.now().isoformat()

        # 4. Adding response to current session
        existing_checkpoint["responses"][timestamp_key] = ResearchState(**response)

        # 5. Maintain audit tracking by logging the execution event
        existing_checkpoint["logs"].append(
            f"Successfully ran workflow for topic: {state.get('topic')} at {timestamp_key}"
        )
        SessionStore.save_progress(request=request, data=existing_checkpoint)

    except ConnectionError:
        print("Connection Timeout")
        return state
    except Exception as e:
        print(f"An unexpected error has occured: {e}")
        return state
    return response


# 2. /json return value will return json file
@app.get("/json")
async def download_json_file(request: Request) -> JSONResponse:

    # 1. Fetches the Object being Saved

    whole_object = request.session.get("current_state")

    # 2. Checking for Null Object

    if not whole_object:
        raise HTTPException(status_code=404, detail="No session data found")

    # 3. Having a filename (**FIX**: Need to put datetime in the name)
    filename = f"current_session_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # 4. Returns JSON Response (Opens up a browser window to download the file)
    return JSONResponse(
        content=whole_object,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# 3. /logs will show logs
# 4. /file returns markdown of research
# 5. /costs returns current sessions costs


if __name__ == "__main__":
    uv.run(app=app)
