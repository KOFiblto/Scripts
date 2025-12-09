from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from api import router as api_router

app = FastAPI()

# CORS - Allow all for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/media/stream")
async def stream_media(path: str):
    """Serve a media file."""
    p = Path(path)
    if not p.exists() or not p.is_file():
        return {"error": "File not found"}
    return FileResponse(p)

# Mount frontend
app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
