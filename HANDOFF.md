# HANDOFF.md - youtuber-debunked

Last updated: 2026-11-17 (Phase 5 Modern Fast Secure Stack & Infomity-Themed Studio completed with 74/74 tests passing).

## Project Overview
`ytdebunk` is an autonomous, 100% zero-recurring-cost "AI Debunker Studio". The platform ingests YouTube videos, performs subtitle-first or Whisper ASR transcription, extracts and classifies claims into typed Pydantic models, conducts agentic web fact-checking (Gemini Grounding + DuckDuckGo), generates persona-driven debunker scripts, synthesizes neural voiceovers (Edge-TTS), synchronizes audio-claim timeline cue sheets, and produces ready-to-publish debunk MP4 videos via FFmpeg/MoviePy.

- **Frontend & API:** Replaced heavy Streamlit interpreter with a modern, fast, secure **FastAPI + Uvicorn** asynchronous backend and an edge-first single-page studio web application.
- **Design System:** Obsidian luxury engineering aesthetic directly integrated from [infomity.github.io](https://infomity.github.io) (`#07090e` obsidian background, radial glow gradients, emerald `#10b981` accents, cyan `#06b6d4`, indigo `#6366f1`, 50px grid lines, and Plus Jakarta Sans / JetBrains Mono typography).
- **Pillars:** 100% zero recurring cost, automated evidence-grounded verification, persona-driven scriptwriting, neural voice synthesis, bilingual (Bengali & English), broadcast video production, ultra-fast secure edge stack.
- **Interfaces:** CLI (`ytdebunk`), Web Studio Server (`ytdebunk-studio` / `python -m ytdebunk.server`).

## Current Status (verified 2026-11-17)
- **Repo:** `https://github.com/hissain/youtuber-debunked` (Public, MIT License).
- **Branch:** `main`.
- **Version:** `1.5.0` in `ytdebunk/__init__.py` and `setup.py`.
- **Test Suite:** **74/74 automated unit tests passing** across 12 test modules in `tests/`.

## Important Decisions
1. **Modern Fast Secure Stack:** Migrated from heavy Streamlit to FastAPI + Uvicorn with an ultra-lightweight, reactive SPA frontend in `ytdebunk/static/index.html`. Zero Python interpreter bottleneck, async non-blocking execution, <50KB total payload.
2. **Infomity Design System:** Themed strictly with the design tokens from `infomity.github.io` (Obsidian `#07090e`, glassmorphic cards `rgba(15, 20, 31, 0.65)`, Emerald `#10b981`, Cyan `#06b6d4`, subtle engineering grid overlay, JetBrains Mono font).
3. **Security:** Directory traversal protection on `/api/download/{filename:path}`, CORS middleware, strict typed Pydantic request validation.
4. **Zero-Cost Constraint:** $0 recurring cost across the entire stack (Google AI Studio free tier, DuckDuckGo search, Edge-TTS, native FFmpeg, local FastAPI server).
5. **Subtitle-First Strategy:** Check for existing YouTube captions before downloading audio and running Whisper ASR (`ytdebunk/subtitles.py`). Saves ~95% processing time.
6. **Persona-Driven Debunker:** Built-in support for 3 personas (`skeptic`, `journalist`, `educator`) with prompt profiles and deterministic fallback templates in English and Bengali.
7. **Free Neural TTS:** Zero-cost neural voice synthesis via Microsoft Edge TTS (`edge-tts`) supporting Bengali and English.
8. **Automated Video Compositor:** High-contrast graphic cards generation (`ytdebunk/graphics.py`) combined with FFmpeg multi-clip concatenation (`ytdebunk/videomaker.py`), supporting 16:9 landscape (`1280x720`) and 9:16 vertical shorts (`720x1280`).

## Technical Context & Code Map
- Workspace: `E:\hissain\github\youtuber-debunked`
- `ytdebunk/server.py`: Modern FastAPI application with REST endpoints (`/`, `/api/analyze`, `/api/voices`, `/api/download/{filename}`).
- `ytdebunk/static/index.html`: Infomity-themed reactive SPA studio dashboard with real-time pipeline status, interactive scorecard, teleprompter, audio player, timeline table, and video player.
- `ytdebunk/ytdebunk.py`: Core CLI orchestrator supporting all pipeline flags (`--verify`, `--script`, `--voice`, `--sync`, `--make_video`, `--aspect_ratio`, etc.).
- `ytdebunk/videomaker.py`: Automated video compositor (`compose_debunk_video`, `render_image_audio_clip`, `concat_video_clips`).
- `ytdebunk/graphics.py`: Visual asset card generator (intro, claim, rebuttal, scorecard).
- `ytdebunk/timeline.py`: Synchronized audio-claim timeline cue sheet generator (`sync_timeline`).
- `ytdebunk/scriptwriter.py`: Persona-driven debunker script generator.
- `ytdebunk/voice.py`: Neural voice synthesis via `edge-tts`.
- `ytdebunk/schema.py`: Pydantic models (`DebunkReport`, `DebunkScript`, `TimelineSheet`, `ClaimVerification`, `ScriptSegment`, `TimelineEvent`, `PersonaType`).
- `ytdebunk/subtitles.py`: Subtitle-first caption probe, VTT parser, and rolling caption deduplicator.
- `ytdebunk/verifier.py`: Live search grounding (`search_ddg`) and agentic Gemini verification pipeline.
- `ytdebunk/downloader.py`: `download_audio(...)` and `download_video(...)` via `yt-dlp`.
- `tests/`: 74 automated unit tests across 12 modules (`test_server.py`, `test_videomaker.py`, `test_timeline.py`, `test_voice.py`, `test_scriptwriter.py`, `test_schema.py`, `test_subtitles.py`, `test_verifier.py`, `test_chunker.py`, `test_cli_args.py`, `test_refiner_philosopher.py`, `test_app.py`).

## Validation
- Executed `python -m pytest tests`: **74/74 passed in 14.85s**.
- Verified FastAPI server routes (`GET /`, `GET /api/voices`, `GET /api/download/`, `POST /api/analyze`).
- Verified directory traversal security prevention on `/api/download/`.
- Verified Infomity CSS color tokens and responsive grid layout.
- Verified CLI and studio server entry points.

## Runbook
- **Environment Setup**:
  ```bash
  python -m venv .venv
  .venv\Scripts\activate   # Windows
  pip install -r requirements.txt
  pip install -e . --no-deps
  ```
- **Ensure FFmpeg**: `ffmpeg -version` must succeed on system PATH.
- **Run Tests**:
  ```bash
  cd youtuber-debunked
  python -m pytest tests
  ```
- **Set API Keys**:
  ```bash
  set GEMINI_API_KEY="your_api_key"
  ```
- **Run Modern Fast Web Studio (FastAPI + Infomity Obsidian UI)**:
  ```bash
  ytdebunk-studio
  # or
  python -m ytdebunk.server
  # Open in browser: http://127.0.0.1:8000
  ```
- **Run CLI**:
  ```bash
  ytdebunk "https://www.youtube.com/watch?v=EXAMPLE" -l en -c -s -w --sync -m -v
  ```
