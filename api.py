from fastapi import FastAPI
import uvicorn as uv


# Creating a test api for now to test scalability and latency along with api costs
app = FastAPI()


# 1. /research endpoint will run the workflow
# 2. /json return value will return json file
# 3. /logs will show logs
# 4. /file returns markdown of research
# 5. /costs returns current sessions costs



