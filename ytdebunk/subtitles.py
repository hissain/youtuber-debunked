import os
import re
import tempfile
import logging
from typing import List, Dict, Optional, Tuple, Any
import yt_dlp
import ytdebunk.settings as settings

logger = logging.getLogger(__name__)

def parse_vtt_timestamp(ts_str: str) -> float:
    """
    Parses a WebVTT timestamp string (HH:MM:SS.mmm or MM:SS.mmm or SS.mmm)
    into seconds as a float.
    """
    ts_str = ts_str.strip()
    parts = ts_str.split(':')
    try:
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        elif len(parts) == 1:
            return float(parts[0])
    except (ValueError, TypeError):
        return 0.0
    return 0.0

def format_seconds(seconds: float) -> str:
    """
    Formats seconds into standard MM:SS or HH:MM:SS string.
    """
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def clean_vtt(
    vtt_content: str,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Parses WebVTT content, cleans tags (e.g. <c>, inline timestamps),
    deduplicates rolling auto-caption lines, filters by start/end times,
    and returns (segments, full_text).
    """
    tag_regex = re.compile(r'<[^>]+>')
    time_regex = re.compile(r'(\d+:\d+(?::\d+)?(?:\.\d+)?)\s*-->\s*(\d+:\d+(?::\d+)?(?:\.\d+)?)')
    
    lines = vtt_content.splitlines()
    segments: List[Dict[str, Any]] = []
    last_cleaned_text = ''
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        time_match = time_regex.search(line)
        if time_match:
            cue_start = parse_vtt_timestamp(time_match.group(1))
            cue_end = parse_vtt_timestamp(time_match.group(2))
            i += 1
            cue_lines = []
            while i < len(lines) and lines[i].strip() and not time_regex.search(lines[i]):
                raw_line = tag_regex.sub('', lines[i]).strip()
                # Remove header/style artifacts
                if raw_line and not any(raw_line.startswith(h) for h in ('WEBVTT', 'NOTE', 'STYLE', 'Kind:', 'Language:')):
                    # Deduplicate rolling auto-caption lines
                    if raw_line != last_cleaned_text and raw_line not in cue_lines:
                        cue_lines.append(raw_line)
                        last_cleaned_text = raw_line
                i += 1
            if cue_lines:
                text = ' '.join(cue_lines).strip()
                # Apply time filtering if bounds provided
                if start_time is not None and cue_end < start_time:
                    continue
                if end_time is not None and cue_start > end_time:
                    continue
                if text:
                    segments.append({
                        'start': cue_start,
                        'end': cue_end,
                        'start_formatted': format_seconds(cue_start),
                        'end_formatted': format_seconds(cue_end),
                        'text': text
                    })
        else:
            i += 1

    full_text = ' '.join(s['text'] for s in segments)
    full_text = re.sub(r'\s+', ' ', full_text).strip()
    return segments, full_text

def get_target_languages(language: str) -> List[str]:
    """
    Returns candidate subtitle language codes matching the target language.
    """
    if language == "bn":
        return ["bn", "bn-BD", "bn-IN", "ben"]
    elif language == "en":
        return ["en", "en-US", "en-GB", "en-CA", "en-AU", "eng"]
    return [language]

def extract_subtitles(
    video_url: str,
    language: str = "en",
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    verbose: bool = False,
    ignore_ssl_cert: bool = False,
    logger: Optional[logging.Logger] = None
) -> Optional[Tuple[List[Dict[str, Any]], str]]:
    """
    Probes for and downloads existing YouTube captions (manual or auto-generated).
    If found, extracts and normalizes the subtitle text, bypassing Whisper ASR.
    Returns (segments, full_text) if successful, or None if no captions exist.
    """
    log = logger or logging.getLogger(__name__)
    target_langs = get_target_languages(language)

    if verbose:
        log.info(f"[ytdebunk-subtitles] Probing for existing captions for {video_url} (langs: {target_langs})...")

    with tempfile.TemporaryDirectory() as tmpdir:
        out_prefix = os.path.join(tmpdir, "subtitle")
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': target_langs,
            'subtitlesformat': 'vtt',
            'outtmpl': out_prefix,
            'noplaylist': True,
            'quiet': not verbose,
            'nocheckcertificate': ignore_ssl_cert,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
        except Exception as e:
            if verbose:
                log.warning(f"[ytdebunk-subtitles] Subtitle download probe encountered an issue: {e}")
            return None

        # Look for downloaded .vtt files
        vtt_files = [
            os.path.join(tmpdir, f)
            for f in os.listdir(tmpdir)
            if f.endswith('.vtt')
        ]

        if not vtt_files:
            if verbose:
                log.info(f"[ytdebunk-subtitles] No subtitles found for {video_url} in requested language ({language}).")
            return None

        # Prefer manual subtitle file or primary language match
        selected_file = vtt_files[0]
        for vf in vtt_files:
            if f".{language}." in vf:
                selected_file = vf
                break

        try:
            with open(selected_file, "r", encoding="utf-8", errors="replace") as fh:
                vtt_content = fh.read()
        except Exception as e:
            if verbose:
                log.warning(f"[ytdebunk-subtitles] Failed to read subtitle file {selected_file}: {e}")
            return None

        segments, full_text = clean_vtt(
            vtt_content,
            start_time=float(start_time) if start_time is not None else None,
            end_time=float(end_time) if end_time is not None else None
        )

        if not full_text.strip():
            if verbose:
                log.info(f"[ytdebunk-subtitles] Subtitle file parsed but extracted text is empty.")
            return None

        log.info(f"[ytdebunk-subtitles] Successfully extracted {len(segments)} subtitle segments ({len(full_text.split())} words) bypassing Whisper!")
        return segments, full_text
