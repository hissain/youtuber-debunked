import os
import sys
import re
import json
import subprocess
import logging
from typing import Optional, List, Tuple, Dict, Any
from ytdebunk.schema import DebunkReport, DebunkScript, TimelineSheet, TimelineEvent
from ytdebunk.graphics import generate_all_graphics, get_dimensions
import ytdebunk.settings as settings

logger = logging.getLogger(__name__)

def check_ffmpeg_available() -> bool:
    """
    Checks whether FFmpeg executable is operational on the host system PATH.
    """
    try:
        res = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return res.returncode == 0
    except Exception:
        return False

def render_image_audio_clip(
    image_path: str,
    duration: float,
    output_clip_path: str,
    audio_path: Optional[str] = None,
    resolution: Tuple[int, int] = (1280, 720)
) -> str:
    """
    Renders a single MP4 video clip combining a static image card and an audio track using FFmpeg.
    If no audio path is provided, generates silent stereo audio track matching duration.
    """
    w, h = resolution
    dur_str = f"{max(0.5, float(duration)):.2f}"
    os.makedirs(os.path.dirname(os.path.abspath(output_clip_path)), exist_ok=True)

    if audio_path and os.path.exists(audio_path):
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", image_path,
            "-i", audio_path,
            "-c:v", "libx264", "-tune", "stillimage",
            "-s", f"{w}x{h}",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", dur_str,
            output_clip_path
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", image_path,
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-c:v", "libx264", "-tune", "stillimage",
            "-s", f"{w}x{h}",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", dur_str,
            "-shortest",
            output_clip_path
        ]

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        err_msg = proc.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"FFmpeg error rendering clip: {err_msg}")

    return output_clip_path

def extract_audio_slice(
    source_audio_path: str,
    start_sec: float,
    end_sec: float,
    output_audio_path: str
) -> str:
    """
    Extracts an audio slice from start_sec to end_sec from source audio using FFmpeg.
    """
    dur = max(0.5, end_sec - start_sec)
    os.makedirs(os.path.dirname(os.path.abspath(output_audio_path)), exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start_sec:.2f}",
        "-t", f"{dur:.2f}",
        "-i", source_audio_path,
        "-c:a", "libmp3lame", "-b:a", "192k",
        output_audio_path
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        err_msg = proc.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"FFmpeg error extracting audio slice: {err_msg}")
    return output_audio_path

def match_quote_to_subtitles(quote: str, subtitles: List[Dict[str, Any]]) -> Tuple[float, float]:
    """
    Matches keywords from quote to subtitle items to infer start and end seconds.
    Expands adjacent matches to capture multi-sentence statements.
    Returns (start_sec, end_sec) or (0.0, 0.0) if no match.
    """
    if not quote or not subtitles:
        return 0.0, 0.0

    clean_quote = re.sub(r'[^\w\s]', ' ', quote.lower())
    words = set([w for w in clean_quote.split() if len(w) > 2])
    if not words:
        return 0.0, 0.0

    matching_indices = []
    for idx, s in enumerate(subtitles):
        txt = (s.get("text") or "").lower()
        cnt = sum(1 for w in words if w in txt)
        if cnt > 0:
            matching_indices.append((idx, cnt))

    if not matching_indices:
        return 0.0, 0.0

    matching_indices.sort(key=lambda x: x[1], reverse=True)
    best_idx = matching_indices[0][0]

    # Expand window around best index if adjacent lines also share words
    start_idx = best_idx
    end_idx = best_idx
    for delta in [-3, -2, -1, 1, 2, 3]:
        cand = best_idx + delta
        if 0 <= cand < len(subtitles):
            txt = (subtitles[cand].get("text") or "").lower()
            if any(w in txt for w in words):
                start_idx = min(start_idx, cand)
                end_idx = max(end_idx, cand)

    from ytdebunk.timeline import parse_timestamp_to_seconds
    s_raw = subtitles[start_idx].get("start") or subtitles[start_idx].get("start_formatted")
    e_raw = subtitles[end_idx].get("end") or subtitles[end_idx].get("end_formatted")
    s_sec = parse_timestamp_to_seconds(s_raw)
    e_sec = parse_timestamp_to_seconds(e_raw)
    if e_sec <= s_sec:
        e_sec = s_sec + 4.0
    return s_sec, e_sec

def render_video_slice(
    source_video_path: str,
    start_sec: float,
    end_sec: float,
    output_clip_path: str,
    resolution: Tuple[int, int] = (1280, 720)
) -> str:
    """
    Extracts an excerpt clip from the source video, scaling/letterboxing to match resolution.
    """
    w, h = resolution
    dur = max(0.5, end_sec - start_sec)
    os.makedirs(os.path.dirname(os.path.abspath(output_clip_path)), exist_ok=True)

    vf_filter = (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start_sec:.2f}",
        "-to", f"{end_sec:.2f}",
        "-i", source_video_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", f"{dur:.2f}",
        output_clip_path
    ]

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        err_msg = proc.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"FFmpeg error extracting video slice: {err_msg}")

    return output_clip_path

def concat_video_clips(clip_paths: List[str], output_path: str) -> str:
    """
    Concatenates a sequence of MP4 clips into the final video using the FFmpeg concat demuxer.
    """
    if not clip_paths:
        raise ValueError("Cannot concatenate empty list of clips.")

    if len(clip_paths) == 1:
        import shutil
        shutil.copy2(clip_paths[0], output_path)
        return output_path

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    manifest_file = os.path.join(os.path.dirname(output_path), "concat_manifest.txt")

    with open(manifest_file, "w", encoding="utf-8") as f:
        for p in clip_paths:
            # Escape path for FFmpeg concat format
            norm_path = os.path.abspath(p).replace("\\", "/")
            f.write(f"file '{norm_path}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", manifest_file,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        output_path
    ]

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if os.path.exists(manifest_file):
        try:
            os.remove(manifest_file)
        except Exception:
            pass

    if proc.returncode != 0:
        err_msg = proc.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"FFmpeg error concatenating clips: {err_msg}")

    return output_path

def compose_debunk_video(
    report: DebunkReport,
    script: DebunkScript,
    timeline: TimelineSheet,
    output_path: Optional[str] = None,
    aspect_ratio: str = "landscape",
    source_video_path: Optional[str] = None,
    source_audio_path: Optional[str] = None,
    keep_temp_clips: bool = False,
    verbose: bool = False,
    logger: Optional[logging.Logger] = None
) -> str:
    """
    Automated zero-cost Debunk Studio Video Compositor:
    1. Generates high-contrast visual reaction cards (PIL).
    2. Renders per-event clips matching the synchronized timeline cue sheet.
    3. Assembles original video excerpts and debunker neural voiceover tracks.
    4. Renders ready-to-publish MP4 in landscape (16:9) or vertical (9:16) format.
    """
    log = logger or logging.getLogger(__name__)

    if not check_ffmpeg_available():
        raise RuntimeError("FFmpeg is required on system PATH for video composition. Please ensure ffmpeg is installed.")

    resolution = get_dimensions(aspect_ratio)
    is_vertical = (aspect_ratio or "").lower() in ["vertical", "portrait", "shorts", "9:16"]

    if output_path:
        final_video_file = output_path
    elif is_vertical:
        final_video_file = getattr(settings, 'DEBUNK_SHORTS_FILE', os.path.join(settings.OUTPUT_DIRECTORY, 'debunk_shorts.mp4'))
    else:
        final_video_file = getattr(settings, 'DEBUNK_VIDEO_FILE', os.path.join(settings.OUTPUT_DIRECTORY, 'debunk_video.mp4'))

    temp_clip_dir = os.path.join(settings.OUTPUT_DIRECTORY, "video_clips")
    os.makedirs(temp_clip_dir, exist_ok=True)

    source_audio = source_audio_path or getattr(settings, 'AUDIO_FILE', None)
    if not (source_audio and os.path.exists(source_audio)):
        default_audio = os.path.join(settings.OUTPUT_DIRECTORY, 'audio.mp3')
        if os.path.exists(default_audio):
            source_audio = default_audio
        else:
            source_audio = None

    if verbose:
        log.info(f"[ytdebunk-videomaker] Starting video composition for {len(timeline.events)} timeline events (Layout: {aspect_ratio}, Res: {resolution[0]}x{resolution[1]})...")

    # Step 1: Generate Visual Cards
    if verbose:
        log.info("[ytdebunk-videomaker] Rendering visual asset cards...")
    cards = generate_all_graphics(report, script, aspect_ratio=aspect_ratio)

    rendered_clips: List[str] = []

    # Step 2: Render each event in sequence
    for idx, ev in enumerate(timeline.events, start=1):
        clip_path = os.path.join(temp_clip_dir, f"clip_{idx:03d}_{ev.event_type}.mp4")

        if verbose:
            log.info(f"[ytdebunk-videomaker] Rendering event #{ev.event_id} ({ev.event_type}, {ev.duration_seconds:.1f}s)...")

        if ev.event_type == "intro":
            card = cards.get("intro")
            audio = ev.audio_file or os.path.join(getattr(settings, 'AUDIO_SEGMENTS_DIR', 'output/audio_segments'), "intro.mp3")
            render_image_audio_clip(
                image_path=card,
                duration=ev.duration_seconds,
                output_clip_path=clip_path,
                audio_path=audio if (audio and os.path.exists(audio)) else None,
                resolution=resolution
            )

        elif ev.event_type == "original_claim":
            slice_success = False
            from ytdebunk.timeline import parse_timestamp_to_seconds

            claim_obj = next((c for c in report.claims if c.id == ev.claim_id), None)
            s_sec = 0.0
            e_sec = 0.0

            if claim_obj and claim_obj.timestamp_start and claim_obj.timestamp_end:
                s_sec = parse_timestamp_to_seconds(claim_obj.timestamp_start)
                e_sec = parse_timestamp_to_seconds(claim_obj.timestamp_end)

            # If claim object lacked timestamps, match quote from subtitles
            if (e_sec <= s_sec) and claim_obj and claim_obj.original_quote:
                subtitles_file = getattr(settings, 'SUBTITLES_JSON_FILE', os.path.join(settings.OUTPUT_DIRECTORY, 'subtitles.json'))
                if os.path.exists(subtitles_file):
                    try:
                        with open(subtitles_file, "r", encoding="utf-8") as sf:
                            sub_data = json.load(sf)
                        m_start, m_end = match_quote_to_subtitles(claim_obj.original_quote, sub_data)
                        if m_end > m_start:
                            s_sec = m_start
                            e_sec = m_end
                    except Exception as e:
                        log.debug(f"[ytdebunk-videomaker] Subtitle matching error: {e}")

            clip_dur = ev.duration_seconds
            if e_sec > s_sec:
                clip_dur = max(1.5, e_sec - s_sec)

            # Option 1: Slicing source video if provided and exists
            if source_video_path and os.path.exists(source_video_path) and e_sec > s_sec:
                try:
                    render_video_slice(
                        source_video_path=source_video_path,
                        start_sec=s_sec,
                        end_sec=e_sec,
                        output_clip_path=clip_path,
                        resolution=resolution
                    )
                    slice_success = True
                except Exception as e:
                    log.warning(f"[ytdebunk-videomaker] Could not slice source video: {e}. Falling back to graphic card + audio.")

            # Option 2: Graphic card + YouTuber's extracted audio slice
            if not slice_success:
                card = cards.get(f"claim_{ev.claim_id}") or cards.get("intro")
                claim_audio_path = None

                if source_audio and os.path.exists(source_audio):
                    try:
                        extracted_audio = os.path.join(temp_clip_dir, f"claim_audio_{ev.claim_id}.mp3")
                        slice_end = e_sec if e_sec > s_sec else (s_sec + clip_dur)
                        extract_audio_slice(
                            source_audio_path=source_audio,
                            start_sec=s_sec,
                            end_sec=slice_end,
                            output_audio_path=extracted_audio
                        )
                        if os.path.exists(extracted_audio):
                            claim_audio_path = extracted_audio
                    except Exception as e:
                        log.warning(f"[ytdebunk-videomaker] Could not slice audio for claim #{ev.claim_id}: {e}")

                render_image_audio_clip(
                    image_path=card,
                    duration=clip_dur,
                    output_clip_path=clip_path,
                    audio_path=claim_audio_path,
                    resolution=resolution
                )

        elif ev.event_type == "debunk_rebuttal":
            card = cards.get(f"rebuttal_{ev.claim_id}") or cards.get("intro")
            audio = ev.audio_file
            if not audio or not os.path.exists(audio):
                audio = os.path.join(getattr(settings, 'AUDIO_SEGMENTS_DIR', 'output/audio_segments'), f"segment_{ev.claim_id}.mp3")

            render_image_audio_clip(
                image_path=card,
                duration=ev.duration_seconds,
                output_clip_path=clip_path,
                audio_path=audio if (audio and os.path.exists(audio)) else None,
                resolution=resolution
            )

        elif ev.event_type == "outro":
            card = cards.get("outro")
            audio = ev.audio_file or os.path.join(getattr(settings, 'AUDIO_SEGMENTS_DIR', 'output/audio_segments'), "outro.mp3")
            render_image_audio_clip(
                image_path=card,
                duration=ev.duration_seconds,
                output_clip_path=clip_path,
                audio_path=audio if (audio and os.path.exists(audio)) else None,
                resolution=resolution
            )

        rendered_clips.append(clip_path)

    # Step 3: Concatenate all clips into final video
    if verbose:
        log.info(f"[ytdebunk-videomaker] Assembling {len(rendered_clips)} clips into {final_video_file}...")

    concat_video_clips(rendered_clips, final_video_file)

    # Step 4: Cleanup temporary clips if not requested to keep
    if not keep_temp_clips:
        for c in rendered_clips:
            try:
                if os.path.exists(c):
                    os.remove(c)
            except Exception:
                pass

    if verbose:
        log.info(f"[ytdebunk-videomaker] Video rendering complete! Saved at {final_video_file}")

    return final_video_file
