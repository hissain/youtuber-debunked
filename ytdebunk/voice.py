import os
import sys
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict, Any
from ytdebunk.schema import DebunkScript, ScriptSegment
import ytdebunk.settings as settings

logger = logging.getLogger(__name__)

# Default voices for zero-cost neural speech synthesis
VOICE_MAP = {
    "en": {
        "male": "en-US-GuyNeural",
        "female": "en-US-JennyNeural"
    },
    "bn": {
        "male": "bn-BD-PradeepNeural",
        "female": "bn-BD-NabanitaNeural"
    }
}

ALL_PRESET_VOICES = [
    {"name": "en-US-GuyNeural", "language": "en", "gender": "male", "label": "English (US) - Guy (Male)"},
    {"name": "en-US-JennyNeural", "language": "en", "gender": "female", "label": "English (US) - Jenny (Female)"},
    {"name": "en-US-ChristopherNeural", "language": "en", "gender": "male", "label": "English (US) - Christopher (Male)"},
    {"name": "en-US-AvaNeural", "language": "en", "gender": "female", "label": "English (US) - Ava (Female)"},
    {"name": "bn-BD-PradeepNeural", "language": "bn", "gender": "male", "label": "Bengali (BD) - Pradeep (Male)"},
    {"name": "bn-BD-NabanitaNeural", "language": "bn", "gender": "female", "label": "Bengali (BD) - Nabanita (Female)"},
    {"name": "bn-IN-BashkarNeural", "language": "bn", "gender": "male", "label": "Bengali (IN) - Bashkar (Male)"},
    {"name": "bn-IN-TanishaaNeural", "language": "bn", "gender": "female", "label": "Bengali (IN) - Tanishaa (Female)"},
]

def get_default_voice(language: str = "en", gender: str = "male") -> str:
    """
    Returns the optimal default neural voice short name for the specified language and gender.
    """
    lang = (language or "en").lower()
    gen = (gender or "male").lower()
    if lang not in VOICE_MAP:
        lang = "en"
    if gen not in VOICE_MAP[lang]:
        gen = "male"
    return VOICE_MAP[lang][gen]

def list_available_voices(language: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns preset high-quality neural voices filtered by language if specified.
    """
    if not language:
        return ALL_PRESET_VOICES
    lang = language.lower()
    return [v for v in ALL_PRESET_VOICES if v["language"] == lang]

def get_audio_duration(file_path: str, fallback_text: Optional[str] = None) -> float:
    """
    Computes precise audio duration in seconds.
    Tries mutagen (MP3), wave (WAV), and falls back to text-length word count estimation.
    """
    if os.path.exists(file_path):
        try:
            from mutagen.mp3 import MP3
            audio = MP3(file_path)
            if audio.info and audio.info.length:
                return round(float(audio.info.length), 3)
        except Exception:
            pass

        try:
            import wave
            with wave.open(file_path, 'r') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0:
                    return round(frames / float(rate), 3)
        except Exception:
            pass

        try:
            # File size approximation for 128kbps MP3 (16 KB/s)
            size_bytes = os.path.getsize(file_path)
            if size_bytes > 0:
                return round(size_bytes / 16000.0, 3)
        except Exception:
            pass

    # Fallback heuristic: conversational speech ~2.5 words per second
    if fallback_text:
        words = len(fallback_text.split())
        return round(max(1.0, words / 2.5), 2)

    return 2.0

async def synthesize_speech_async(
    text: str,
    output_path: str,
    voice: Optional[str] = None,
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%"
) -> str:
    """
    Asynchronously synthesizes speech using edge-tts and writes to output_path.
    """
    import edge_tts
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    voice_name = voice or get_default_voice("en", "male")
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice_name,
        rate=rate,
        pitch=pitch,
        volume=volume
    )
    await communicate.save(output_path)
    return output_path

def _run_in_new_loop(coro):
    new_loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(new_loop)
        return new_loop.run_until_complete(coro)
    finally:
        new_loop.close()

def synthesize_speech(
    text: str,
    output_path: str,
    voice: Optional[str] = None,
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%"
) -> str:
    """
    Synchronous thread-safe entry point for neural speech synthesis.
    Works seamlessly inside running event loops (e.g. Streamlit or asyncio) by delegating to a worker thread if needed.
    """
    coro = synthesize_speech_async(
        text=text,
        output_path=output_path,
        voice=voice,
        rate=rate,
        pitch=pitch,
        volume=volume
    )

    try:
        # Check if an event loop is already running
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        # Inside active event loop: delegate to a worker thread to avoid loop conflict
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_in_new_loop, coro)
            return future.result()
    else:
        return asyncio.run(coro)

def synthesize_script(
    script: DebunkScript,
    voice: Optional[str] = None,
    gender: str = "male",
    output_dir: Optional[str] = None,
    combine_full: bool = True,
    verbose: bool = False,
    logger: Optional[logging.Logger] = None
) -> DebunkScript:
    """
    Synthesizes neural voiceover audio for every segment of a DebunkScript:
    - intro.mp3
    - segment_{id}.mp3
    - outro.mp3
    - debunk_voiceover.mp3 (complete narration)
    Updates script segment audio paths and precise durations in-place.
    """
    log = logger or logging.getLogger(__name__)
    chosen_voice = voice or get_default_voice(script.language, gender)
    target_dir = output_dir or getattr(settings, 'AUDIO_SEGMENTS_DIR', os.path.join(settings.OUTPUT_DIRECTORY, 'audio_segments'))
    os.makedirs(target_dir, exist_ok=True)

    if verbose:
        log.info(f"[ytdebunk-voice] Synthesizing DebunkScript voiceover with voice='{chosen_voice}'...")

    # 1. Synthesize Intro / Hook
    intro_path = os.path.join(target_dir, "intro.mp3")
    try:
        synthesize_speech(script.hook, intro_path, voice=chosen_voice)
        intro_dur = get_audio_duration(intro_path, fallback_text=script.hook)
        if verbose:
            log.info(f"[ytdebunk-voice] Synthesized intro audio ({intro_dur:.2f}s) -> {intro_path}")
    except Exception as e:
        log.warning(f"[ytdebunk-voice] Error synthesizing intro: {e}")
        intro_dur = get_audio_duration(intro_path, fallback_text=script.hook)

    # 2. Synthesize Segments
    for seg in script.segments:
        seg_file = f"segment_{seg.segment_id}.mp3"
        seg_path = os.path.join(target_dir, seg_file)
        try:
            synthesize_speech(seg.rebuttal_text, seg_path, voice=chosen_voice)
            dur = get_audio_duration(seg_path, fallback_text=seg.rebuttal_text)
            seg.audio_path = seg_path
            seg.duration_seconds = dur
            if verbose:
                log.info(f"[ytdebunk-voice] Segment #{seg.segment_id} synthesized ({dur:.2f}s) -> {seg_path}")
        except Exception as e:
            log.warning(f"[ytdebunk-voice] Error synthesizing segment #{seg.segment_id}: {e}")
            seg.duration_seconds = get_audio_duration(seg_path, fallback_text=seg.rebuttal_text)

    # 3. Synthesize Outro
    outro_path = os.path.join(target_dir, "outro.mp3")
    try:
        synthesize_speech(script.outro, outro_path, voice=chosen_voice)
        outro_dur = get_audio_duration(outro_path, fallback_text=script.outro)
        if verbose:
            log.info(f"[ytdebunk-voice] Synthesized outro audio ({outro_dur:.2f}s) -> {outro_path}")
    except Exception as e:
        log.warning(f"[ytdebunk-voice] Error synthesizing outro: {e}")
        outro_dur = get_audio_duration(outro_path, fallback_text=script.outro)

    # 4. Synthesize Full Continuous Voiceover Track
    if combine_full:
        full_text = script.get_full_narration()
        full_audio_path = getattr(settings, 'FULL_DEBUNK_AUDIO', os.path.join(settings.OUTPUT_DIRECTORY, 'debunk_voiceover.mp3'))
        try:
            synthesize_speech(full_text, full_audio_path, voice=chosen_voice)
            full_dur = get_audio_duration(full_audio_path, fallback_text=full_text)
            script.audio_path = full_audio_path
            script.total_duration_seconds = full_dur
            if verbose:
                log.info(f"[ytdebunk-voice] Full narration synthesized ({full_dur:.2f}s) -> {full_audio_path}")
        except Exception as e:
            log.warning(f"[ytdebunk-voice] Error synthesizing full voiceover: {e}")
            calc_dur = intro_dur + sum(s.duration_seconds or 0 for s in script.segments) + outro_dur
            script.total_duration_seconds = round(calc_dur, 2)
    else:
        calc_dur = intro_dur + sum(s.duration_seconds or 0 for s in script.segments) + outro_dur
        script.total_duration_seconds = round(calc_dur, 2)

    # Persist updated script metadata with audio paths
    script.save()
    return script
