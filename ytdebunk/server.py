import os
import sys
import logging

# Ensure UTF-8 output streams on Windows to prevent UnicodeEncodeError with cp1252
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
import threading
from collections import deque
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import ytdebunk.settings as settings
from ytdebunk.voice import list_available_voices, get_default_voice
from ytdebunk.ytdebunk import main as ytdebunk_main, DebunkResult

logger = logging.getLogger(__name__)

class LogCaptureHandler(logging.Handler):
    """
    Thread-safe in-memory log buffer for real-time inspection in the studio UI.
    """
    def __init__(self, capacity: int = 2000):
        super().__init__()
        self.capacity = capacity
        self.records = deque(maxlen=capacity)
        self._lock = threading.Lock()

    def emit(self, record):
        try:
            msg = self.format(record)
            with self._lock:
                self.records.append(msg)
        except Exception:
            self.handleError(record)

    def get_logs(self, limit: int = 100) -> List[str]:
        with self._lock:
            recs = list(self.records)
            return recs[-limit:] if limit > 0 else recs

    def clear(self):
        with self._lock:
            self.records.clear()

# Initialize log capture handler
log_capture = LogCaptureHandler(capacity=2000)
log_capture.setLevel(logging.INFO)
log_capture.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))

# Attach to root and module loggers with INFO level
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(log_capture)

ytdebunk_logger = logging.getLogger("ytdebunk")
ytdebunk_logger.setLevel(logging.INFO)
ytdebunk_logger.addHandler(log_capture)

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

class SaveKeyRequest(BaseModel):
    key: str = Field(description="Gemini API Key to persist")

@app.get("/", response_class=HTMLResponse)
def serve_studio():
    """
    Serves the Infomity-themed AI Debunker Studio Web Dashboard.
    """
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="Studio frontend not found.")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/config")
def get_config():
    """
    Returns server status and whether a Gemini API key is configured in the environment.
    """
    has_env_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GENAI_API_KEY"))
    return {
        "status": "ready",
        "has_gemini_key": has_env_key,
        "version": "1.5.0",
        "output_directory": settings.OUTPUT_DIRECTORY
    }

@app.get("/api/logs")
def get_logs(limit: int = Query(default=100, ge=1, le=1000)):
    """
    Returns recent server and pipeline log lines.
    """
    return {"logs": log_capture.get_logs(limit=limit)}

@app.post("/api/save_key")
def save_gemini_key(req: SaveKeyRequest):
    """
    Persists the Gemini API key in os.environ and the local .env file.
    """
    cleaned_key = req.key.strip()
    if not cleaned_key:
        raise HTTPException(status_code=400, detail="API key cannot be empty.")

    os.environ["GEMINI_API_KEY"] = cleaned_key
    logger.info("[ytdebunk-server] Updated GEMINI_API_KEY in process environment.")

    # Persist to .env in repository root
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(repo_root, ".env")
    lines = []
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                lines = [l for l in f.readlines() if not l.startswith("GEMINI_API_KEY=") and not l.startswith("GENAI_API_KEY=")]
        except Exception as e:
            logger.warning(f"[ytdebunk-server] Could not read existing .env: {e}")

    lines.append(f"GEMINI_API_KEY={cleaned_key}\n")
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        logger.info(f"[ytdebunk-server] Persisted GEMINI_API_KEY to {env_path}")
    except Exception as e:
        logger.error(f"[ytdebunk-server] Could not write to .env: {e}")

    return {"status": "ok", "message": "Gemini API key saved successfully."}

@app.get("/api/voices")
def get_voices(language: Optional[str] = Query(None)):
    """
    Returns available neural TTS voices for English and Bengali.
    """
    return list_available_voices(language=language)

@app.post("/api/analyze")
def analyze_video(req: AnalyzeRequest):
    """
    Executes the autonomous debunk pipeline according to request configuration.
    Runs synchronously in FastAPI worker threadpool so the event loop is never blocked.
    """
    if not req.video_url or not req.video_url.strip():
        raise HTTPException(status_code=400, detail="Missing required video_url.")

    token = req.token or os.getenv("GEMINI_API_KEY") or os.getenv("GENAI_API_KEY")
    requires_gemini = req.verify or req.script or req.enhance or req.detect

    if requires_gemini and not token:
        logger.warning("[ytdebunk-server] Verification or analysis requested without a Gemini API token.")
        raise HTTPException(
            status_code=400,
            detail=(
                "Gemini API Key is required for Verification, Scriptwriting, and Fallacy Detection. "
                "Please enter your Gemini API key in the 'Gemini API Token' field on the dashboard, "
                "or uncheck those stages to run subtitle/audio extraction only."
            )
        )

    logs_start_idx = len(log_capture.records)

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
    if token:
        cli_args.extend(["--token", token])

    cli_args.append("--ignore_ssl")
    cli_args.append("--verbose")

    # Run through core orchestrator
    old_argv = sys.argv
    try:
        sys.argv = ["ytdebunk"] + cli_args
        logger.info(f"[ytdebunk-server] Starting pipeline execution for: {req.video_url}")
        result = ytdebunk_main()
    except Exception as e:
        logger.exception(f"[ytdebunk-server] Pipeline failed with unhandled exception: {e}")
        run_logs = list(log_capture.records)[logs_start_idx:]
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")
    finally:
        sys.argv = old_argv

    run_logs = list(log_capture.records)[logs_start_idx:]

    if result is None or (isinstance(result, tuple) and len(result) > 0 and result[0] is None):
        err_msg = "Debunk pipeline did not produce output. Check the server logs."
        for line in reversed(run_logs):
            if "ERROR" in line or "error" in line.lower():
                err_msg = line
                break
        logger.error(f"[ytdebunk-server] Pipeline terminated unsuccessfully: {err_msg}")
        raise HTTPException(status_code=500, detail=err_msg)

    transcription = result[0] if len(result) > 0 else ""
    logical_faults = result[1] if len(result) > 1 else None
    report = getattr(result, "report", None)
    script = getattr(result, "script", None)
    timeline = getattr(result, "timeline", None)
    video_path = getattr(result, "video_path", None)

    logger.info(f"[ytdebunk-server] Pipeline completed successfully for {req.video_url}")

    return {
        "transcription": transcription,
        "logical_faults": logical_faults,
        "report": report.model_dump() if report else None,
        "script": script.model_dump() if script else None,
        "timeline": timeline.model_dump() if timeline else None,
        "video_path": video_path,
        "logs": run_logs
    }

@app.get("/api/download/{filename:path}")
def download_file(filename: str):
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
    print(f"\n[ytdebunk-studio] AI Debunker Studio running at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run()
