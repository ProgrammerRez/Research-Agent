"""
Root API Execution Layer
========================
Launches the FastAPI application engine gateway directly from the workspace root
context, ensuring the 'schema' folder package namespace is cleanly evaluated.
"""

import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    # Host and Port configuration parameters
    HOST = os.getenv("API_HOST", "0.0.0.0")
    PORT = int(os.getenv("API_PORT", 8000))

    print(f"📡 Initializing Uvicorn Gateway Loop from workspace root context...")
    print(f"🔗 Target Endpoint: http://{HOST}:{PORT}")

    # Crucial Step: Point Uvicorn to the module nested inside your api/ folder
    # "api.api:app" means: look inside the 'api' directory, open 'api.py', find 'app'
    uvicorn.run("api.api:app", host=HOST, port=PORT, reload=True)
