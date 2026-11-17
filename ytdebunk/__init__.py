"""
ytdebunk - Autonomous AI Debunker Studio: Ingests YouTube videos, extracts captions, verifies claims, writes persona scripts, synthesizes neural voiceover, and renders debunk videos.
"""

__version__ = "1.5.0"

from ytdebunk.schema import (
    DebunkReport,
    ClaimVerification,
    DebunkScript,
    ScriptSegment,
    TimelineSheet,
    TimelineEvent,
    PersonaType,
    ClaimType,
    VeracityRating,
    FallacyType
)
from ytdebunk.scriptwriter import generate_debunk_script
from ytdebunk.voice import synthesize_speech, synthesize_script, get_default_voice
from ytdebunk.timeline import sync_timeline
from ytdebunk.graphics import generate_all_graphics
from ytdebunk.videomaker import compose_debunk_video, check_ffmpeg_available
from ytdebunk.downloader import download_video
from ytdebunk.server import app as studio_app, run as run_studio
