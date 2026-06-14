"""./run_api.py
    This file primarily runs the api
"""

import uvicorn as uv
from api.api import app

if __name__ == "__main__":
    uv.run(app=app)
