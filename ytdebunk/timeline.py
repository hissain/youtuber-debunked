import os
import re
import json
import logging
from typing import Optional, List, Dict, Any
from ytdebunk.schema import DebunkReport, DebunkScript, TimelineSheet, TimelineEvent
import ytdebunk.settings as settings

logger = logging.getLogger(__name__)

def parse_timestamp_to_seconds(ts: Optional[str]) -> float:
    """
    Parses a timestamp string ('MM:SS', 'HH:MM:SS', 'SS', or decimal) into seconds float.
    Returns 0.0 if None or invalid.
    """
    if not ts:
        return 0.0

    cleaned = str(ts).strip()
    # Check for direct numeric float/int string
    try:
        return max(0.0, float(cleaned))
    except ValueError:
        pass

    # Split by colon
    parts = cleaned.split(":")
    try:
        if len(parts) == 3:  # HH:MM:SS
            h = float(parts[0])
            m = float(parts[1])
            s = float(parts[2])
            return h * 3600.0 + m * 60.0 + s
        elif len(parts) == 2:  # MM:SS
            m = float(parts[0])
            s = float(parts[1])
            return m * 60.0 + s
        elif len(parts) == 1:
            return float(parts[0])
    except ValueError:
        pass

    return 0.0

def format_seconds_to_timestamp(seconds: float) -> str:
    """
    Formats seconds float into a human-readable 'MM:SS' or 'HH:MM:SS' string.
    """
    total_sec = max(0, int(round(seconds)))
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    secs = total_sec % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def sync_timeline(
    report: DebunkReport,
    script: DebunkScript,
    mode: str = "interleaved",
    verbose: bool = False,
    logger: Optional[logging.Logger] = None
) -> TimelineSheet:
    """
    Synchronizes original video claim segments and synthesized debunker audio segments
    into a precise, unified video editing timeline cue sheet.
    
    Modes:
    - 'interleaved': Sequential reaction pattern (Intro -> [Claim Excerpt -> Rebuttal Audio] -> Outro).
    - 'side_by_side': Synchronized timestamp tracking anchored to the original video time-code.
    """
    log = logger or logging.getLogger(__name__)
    events: List[TimelineEvent] = []
    current_time = 0.0
    event_idx = 1

    if verbose:
        log.info(f"[ytdebunk-timeline] Synchronizing timeline in mode='{mode}' for {len(report.claims)} claims...")

    # Determine Intro Duration
    intro_audio = os.path.join(getattr(settings, 'AUDIO_SEGMENTS_DIR', 'output/audio_segments'), "intro.mp3")
    if os.path.exists(intro_audio):
        from ytdebunk.voice import get_audio_duration
        intro_dur = get_audio_duration(intro_audio, fallback_text=script.hook)
    else:
        intro_words = len(script.hook.split())
        intro_dur = round(max(2.5, intro_words / 2.5), 2)

    # 1. Event: Intro / Hook
    intro_end = round(current_time + intro_dur, 2)
    events.append(
        TimelineEvent(
            event_id=event_idx,
            claim_id=None,
            event_type="intro",
            title="Studio Hook & Introduction",
            start_seconds=round(current_time, 2),
            end_seconds=intro_end,
            timestamp_start=format_seconds_to_timestamp(current_time),
            timestamp_end=format_seconds_to_timestamp(intro_end),
            duration_seconds=intro_dur,
            text=script.hook,
            audio_file=intro_audio if os.path.exists(intro_audio) else None,
            cue="Display Debunker Title Card & Topic Headline"
        )
    )
    current_time = intro_end
    event_idx += 1

    # Index script segments by claim_id for robust pairing
    segments_by_claim = {seg.claim_id: seg for seg in script.segments if seg.claim_id is not None}

    # 2. Events: Paired Claim Excerpts and Debunker Rebuttals
    for idx, claim in enumerate(report.claims, start=1):
        seg = segments_by_claim.get(claim.id)
        if seg is None and idx <= len(script.segments):
            seg = script.segments[idx - 1]

        # A. Original Claim Video Excerpt
        claim_ts_start = parse_timestamp_to_seconds(claim.timestamp_start)
        claim_ts_end = parse_timestamp_to_seconds(claim.timestamp_end)
        if claim_ts_end > claim_ts_start:
            orig_dur = round(claim_ts_end - claim_ts_start, 2)
        else:
            orig_words = len(claim.original_quote.split())
            orig_dur = round(max(3.0, orig_words / 2.5), 2)

        clip_end = round(current_time + orig_dur, 2)
        events.append(
            TimelineEvent(
                event_id=event_idx,
                claim_id=claim.id,
                event_type="original_claim",
                title=f"Original Claim #{claim.id} Video Excerpt",
                start_seconds=round(current_time, 2),
                end_seconds=clip_end,
                timestamp_start=format_seconds_to_timestamp(current_time),
                timestamp_end=format_seconds_to_timestamp(clip_end),
                duration_seconds=orig_dur,
                text=claim.original_quote,
                audio_file=None,
                veracity=claim.veracity,
                cue=f"Cut to source video clip ({claim.timestamp_start or '00:00'} - {claim.timestamp_end or '--:--'})"
            )
        )
        current_time = clip_end
        event_idx += 1

        # B. Debunker Rebuttal Audio
        if seg and seg.duration_seconds:
            rebuttal_dur = seg.duration_seconds
        elif seg and seg.audio_path and os.path.exists(seg.audio_path):
            from ytdebunk.voice import get_audio_duration
            rebuttal_dur = get_audio_duration(seg.audio_path, fallback_text=seg.rebuttal_text)
        elif seg:
            rebuttal_dur = round(max(2.5, len(seg.rebuttal_text.split()) / 2.5), 2)
        else:
            rebuttal_text = claim.counter_argument or claim.evidence_summary
            rebuttal_dur = round(max(2.5, len(rebuttal_text.split()) / 2.5), 2)

        rebuttal_end = round(current_time + rebuttal_dur, 2)
        rebuttal_text = seg.rebuttal_text if seg else (claim.counter_argument or claim.evidence_summary)
        seg_audio = seg.audio_path if (seg and seg.audio_path and os.path.exists(seg.audio_path)) else None
        source_citation = claim.sources[0] if claim.sources else ""
        default_cue = f"Display '{claim.veracity.upper()}' badge"
        if source_citation:
            default_cue += f" | Source: {source_citation}"

        events.append(
            TimelineEvent(
                event_id=event_idx,
                claim_id=claim.id,
                event_type="debunk_rebuttal",
                title=f"Debunker Rebuttal: Claim #{claim.id} ({claim.veracity})",
                start_seconds=round(current_time, 2),
                end_seconds=rebuttal_end,
                timestamp_start=format_seconds_to_timestamp(current_time),
                timestamp_end=format_seconds_to_timestamp(rebuttal_end),
                duration_seconds=rebuttal_dur,
                text=rebuttal_text,
                audio_file=seg_audio,
                veracity=claim.veracity,
                cue=seg.visual_cue if (seg and seg.visual_cue) else default_cue
            )
        )
        current_time = rebuttal_end
        event_idx += 1

    # 3. Event: Outro / Verdict
    outro_audio = os.path.join(getattr(settings, 'AUDIO_SEGMENTS_DIR', 'output/audio_segments'), "outro.mp3")
    if os.path.exists(outro_audio):
        from ytdebunk.voice import get_audio_duration
        outro_dur = get_audio_duration(outro_audio, fallback_text=script.outro)
    else:
        outro_words = len(script.outro.split())
        outro_dur = round(max(2.5, outro_words / 2.5), 2)

    outro_end = round(current_time + outro_dur, 2)
    events.append(
        TimelineEvent(
            event_id=event_idx,
            claim_id=None,
            event_type="outro",
            title="Debunker Final Verdict & Outro",
            start_seconds=round(current_time, 2),
            end_seconds=outro_end,
            timestamp_start=format_seconds_to_timestamp(current_time),
            timestamp_end=format_seconds_to_timestamp(outro_end),
            duration_seconds=outro_dur,
            text=script.outro,
            audio_file=outro_audio if os.path.exists(outro_audio) else None,
            cue=f"Display Final Veracity Scorecard ({report.overall_veracity_score:.1f}%) & Subscribe callout"
        )
    )
    current_time = outro_end

    timeline = TimelineSheet(
        video_url=report.video_url,
        language=script.language,
        total_duration_seconds=round(current_time, 2),
        events=events
    )

    timeline.save()
    if verbose:
        log.info(f"[ytdebunk-timeline] Timeline synchronized: {len(events)} events, total duration: {timeline.total_duration_seconds:.1f}s.")

    return timeline
