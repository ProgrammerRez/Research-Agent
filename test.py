import requests

session = requests.Session()

initial_input = {
    "topic": "Machine Learning Systems Design", 
    "research_mode": "ultra-fast"
}

# 1. Run the workflow
response = session.post(
    url='http://127.0.0.1:8000/research',
    json=initial_input
)

# 2. Hit the download route
file_response = session.get(
    url='http://127.0.0.1:8000/json'
)

if file_response.ok:
    # Extract the filename sent by FastAPI from the headers if you want it exactly
    # Or just hardcode a download path here
    output_filename = "downloaded_session_data.json"
    
    # 3. Read the payload binary content and write it out onto your hard drive
    with open(output_filename, "wb") as f:
        f.write(file_response.content)
        
    print(f"Success! Saved the session file locally as: {output_filename}")
else:
    print(f"Download failed: {file_response.text}")
