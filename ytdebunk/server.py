import os
import sys
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import ytdebunk.settings as settings
from ytdebunk.voice import list_available_voices, get_default_voice
from ytdebunk.ytdebunk import main as ytdebunk_main, DebunkResult

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Debunker Studio API",
    description="High-performance, zero-cost API for YouTube video deconstruction, claim verification, persona scriptwriting, and automated video composition.",
    version="1.5.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    video_url: str = Field(description="Target YouTube video URL")
    start_time: Optional[int] = Field(default=None, description="Start time in seconds")
    end_time: Optional[int] = Field(default=None, description="End time in seconds")
    language: str = Field(default="en", description="'en' or 'bn'")
    persona: str = Field(default="skeptic", description="'skeptic', 'journalist', or 'educator'")
    voice_name: Optional[str] = Field(default=None, description="Neural voice model name")
    voice_gender: str = Field(default="male", description="'male' or 'female'")
    aspect_ratio: str = Field(default="landscape", description="'landscape' or 'vertical'")
    token: Optional[str] = Field(default=None, description="Optional Gemini API key override")
    verify: bool = Field(default=True, description="Verify claims with live search grounding")
    script: bool = Field(default=True, description="Generate debunker character script")
    voice: bool = Field(default=True, description="Synthesize neural voiceover audio")
    sync: bool = Field(default=True, description="Synchronize audio-claim timeline")
    make_video: bool = Field(default=False, description="Render debunk MP4 video")
    force_asr: bool = Field(default=False, description="Skip captions and force Whisper ASR")
    enhance: bool = Field(default=False, description="Enhance transcript with LLM")
    detect: bool = Field(default=True, description="Detect logical fallacies")

@app.get("/", response_class=HTMLResponse)
async def serve_studio():
    """
    Serves the Infomity-themed AI Debunker Studio Web Dashboard.
    """
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="Studio frontend not found.")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/voices")
async def get_voices(language: Optional[str] = Query(None)):
    """
    Returns available neural TTS voices for English and Bengali.
    """
    return list_available_voices(language=language)

@app.post("/api/analyze")
async def analyze_video(req: AnalyzeRequest):
    """
    Executes the autonomous debunk pipeline according to request configuration.
    """
    if not req.video_url or not req.video_url.strip():
        raise HTTPException(status_code=400, detail="Missing required video_url.")

    cli_args = [req.video_url.strip()]

    if req.start_time is not None:
        cli_args.extend(["--start_time", str(req.start_time)])
    if req.end_time is not None:
        cli_args.extend(["--end_time", str(req.end_time)])

    cli_args.extend(["--language", req.language])
    cli_args.extend(["--persona", req.persona])

    if req.voice_name:
        cli_args.extend(["--voice_name", req.voice_name])
    cli_args.extend(["--voice_gender", req.voice_gender])

    if req.verify:
        cli_args.append("--verify")
    if req.script:
        cli_args.append("--script")
    if req.voice:
        cli_args.append("--voice")
    if req.sync:
        cli_args.append("--sync")
    if req.make_video:
        cli_args.append("--make_video")
        cli_args.extend(["--aspect_ratio", req.aspect_ratio])
    if req.force_asr:
        cli_args.append("--force_asr")
    if req.enhance:
        cli_args.append("--enhance")
    if req.detect:
        cli_args.append("--detect")
    if req.token:
        cli_args.extend(["--token", req.token])

    cli_args.append("--ignore_ssl")

    # Run through core orchestrator
    old_argv = sys.argv
    try:
        sys.argv = ["ytdebunk"] + cli_args
        result = ytdebunk_main()
    finally:
        sys.argv = old_argv

    if result is None:
        raise HTTPException(status_code=500, detail="Debunk studio pipeline encountered an error.")

    transcription = result[0] if len(result) > 0 else ""
    logical_faults = result[1] if len(result) > 1 else None
    report = getattr(result, "report", None)
    script = getattr(result, "script", None)
    timeline = getattr(result, "timeline", None)
    video_path = getattr(result, "video_path", None)

    return {
        "transcription": transcription,
        "logical_faults": logical_faults,
        "report": report.model_dump() if report else None,
        "script": script.model_dump() if script else None,
        "timeline": timeline.model_dump() if timeline else None,
        "video_path": video_path
    }

@app.get("/api/download/{filename:path}")
async def download_file(filename: str):
    """
    Secure file download endpoint preventing directory traversal.
    """
    # Prevent directory traversal attacks
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    # Search in output directories
    search_dirs = [
        settings.OUTPUT_DIRECTORY,
        getattr(settings, "AUDIO_SEGMENTS_DIR", os.path.join(settings.OUTPUT_DIRECTORY, "audio_segments")),
        getattr(settings, "GRAPHICS_DIR", os.path.join(settings.OUTPUT_DIRECTORY, "graphics"))
    ]

    target_path = None
    for d in search_dirs:
        cand = os.path.join(d, filename)
        if os.path.exists(cand) and os.path.isfile(cand):
            target_path = cand
            break

    if not target_path:
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found.")

    ext = os.path.splitext(filename)[1].lower()
    media_types = {
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".json": "application/json",
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".png": "image/png"
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(path=target_path, media_type=media_type, filename=filename)

def run(host: str = "127.0.0.1", port: int = 8000):
    """
    Entry point to run the FastAPI studio server with Uvicorn.
    """
    import uvicorn
    print(f"\n🚀 AI Debunker Studio running at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run()
