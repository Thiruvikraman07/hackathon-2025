from fastapi import FastAPI, HTTPException
from pathlib import Path
import uvicorn
import json

app = FastAPI()

LOG_DIR = Path(__file__).parent.parent  # You can set this to your logs folder

@app.get("/logs/combined")
def get_combined_logs():
    if not LOG_DIR.exists():
        return {"error": "execution_logs folder not found"}

    files = [
        f.name
        for f in LOG_DIR.iterdir()
        if f.is_file() and "_combined_frontend_logs.json" in f.name.lower()
    ]

    return {"files": files}


@app.get("/logs/file/{file_name}")
def get_log_file(file_name: str):
    print("Requested file:", file_name)
    file_path = LOG_DIR / file_name
    print("Full path:", file_path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="File is not a valid JSON")
    
    return data



if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
