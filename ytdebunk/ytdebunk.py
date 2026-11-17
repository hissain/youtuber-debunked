import argparse
import os
import sys
import json
import logging
import ytdebunk.settings as settings
from dotenv import load_dotenv
from ytdebunk.downloader import download_audio
from ytdebunk.transcriber import transcribe_audio
from ytdebunk.refiner import enhance_transcription
from ytdebunk.philosopher import detect_logical_faults
from ytdebunk.subtitles import extract_subtitles
from ytdebunk.verifier import verify_claims
from ytdebunk.scriptwriter import generate_debunk_script
from ytdebunk.voice import synthesize_script, get_default_voice
from ytdebunk.timeline import sync_timeline
from ytdebunk.videomaker import compose_debunk_video

load_dotenv()

class DebunkResult(tuple):
    """
    Backwards-compatible return tuple that unpacks as (transcription, logical_faults)
    while exposing .report, .script, .timeline, .video_path, .transcription, and .logical_faults attributes.
    """
    def __new__(cls, transcription, logical_faults, report=None, script=None, timeline=None, video_path=None):
        return super().__new__(cls, (transcription, logical_faults))

    def __init__(self, transcription, logical_faults, report=None, script=None, timeline=None, video_path=None):
        self.transcription = transcription
        self.logical_faults = logical_faults
        self.report = report
        self.script = script
        self.timeline = timeline
        self.video_path = video_path

def main():
    parser = argparse.ArgumentParser(description="This command aims to automate the extraction of audio/subtitles from a given YouTube video link, transcribe or extract the content, and analyze the transcriptions using Agentic AI to identify logical fallacies, verify claims via live web search, and generate structured Debunk Reports.")
    parser.add_argument("yt_video_url", type=str, help="URL of the YouTube video (shorts, video) to be analyzed")
    parser.add_argument("-l", "--language", type=str, default="en", help="Language (code) of the transcription. Valid: [bn, en], default: en")
    parser.add_argument("-e", "--enhance", action="store_true", default=False, help="Enhance the transcription")
    parser.add_argument("-d", "--detect", action="store_true", default=False, help="Detect logical fallacies, bias, irony, faults in the transcription")
    parser.add_argument("-c", "--verify", action="store_true", default=False, help="Extract verifiable claims, ground evidence via live web search, and generate a structured Debunk Report (Pydantic)")
    parser.add_argument("-s", "--script", action="store_true", default=False, help="Generate persona-driven Debunker script (Skeptic, Journalist, Educator)")
    parser.add_argument("-w", "--voice", action="store_true", default=False, help="Synthesize neural voiceover audio using Edge-TTS")
    parser.add_argument("--persona", type=str, default="skeptic", choices=["skeptic", "journalist", "educator"], help="Debunker persona style (default: skeptic)")
    parser.add_argument("--voice_name", type=str, default=None, help="Edge-TTS voice override (e.g. bn-BD-PradeepNeural, en-US-GuyNeural)")
    parser.add_argument("--voice_gender", type=str, default="male", choices=["male", "female"], help="Voice gender (default: male)")
    parser.add_argument("--sync", action="store_true", default=False, help="Build synchronized audio-claim timeline cue sheet")
    parser.add_argument("-m", "--make_video", action="store_true", default=False, help="Render ready-to-publish debunk MP4 video")
    parser.add_argument("--aspect_ratio", type=str, default="landscape", choices=["landscape", "vertical"], help="Video layout: landscape (16:9) or vertical (9:16)")
    parser.add_argument("--force_asr", action="store_true", default=False, help="Force audio download and Whisper ASR even if YouTube captions/subtitles exist")
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help="Increase output verbosity")
    parser.add_argument("-t", "--token", type=str, help="API token for the Gemini API")
    parser.add_argument("-st", "--start_time", type=int, default=None, help="Start time of the audio clip in seconds for transcription")
    parser.add_argument("-et", "--end_time", type=int, default=None, help="End time of the audio clip in seconds for transcription")
    parser.add_argument("-is", "--ignore_ssl", action="store_true", default=False, help="Ignore SSL certificate errors (nocheckcertificate)")

    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    logger = logging.getLogger(__name__)

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

    if args.verbose:
        logger.info(f"[ytdebunk] Analyzing YouTube video: {args.yt_video_url}")
        logger.info(f"[ytdebunk] Language: {args.language}")
        logger.info(f"[ytdebunk] Enhance: {args.enhance}")
        logger.info(f"[ytdebunk] Detect: {args.detect}")
        logger.info(f"[ytdebunk] Verify: {args.verify}")
        logger.info(f"[ytdebunk] Force ASR: {args.force_asr}")
        logger.info(f"[ytdebunk] Start Time: {args.start_time}")
        logger.info(f"[ytdebunk] End Time: {args.end_time}")
        logger.info(f"[ytdebunk] Ignore SSL: {args.ignore_ssl}")
        logger.info(f"[ytdebunk] Verbose: {args.verbose}")

    token = args.token or os.getenv("GEMINI_API_KEY") or os.getenv("GENAI_API_KEY")

    if args.enhance or args.detect or args.verify:
        if not token:
            logger.error("[ytdebunk] Enhancement, detection, or verification is enabled, but no Gemini API token was provided via --token or found in GEMINI_API_KEY / GENAI_API_KEY environment variables.")
            return None, None
        if args.token:
            logger.info("[ytdebunk] Using Gemini API token from command-line argument.")
        else:
            logger.info("[ytdebunk] Using Gemini API token from environment variable.")

    st = args.start_time
    et = args.end_time
    ln = args.language

    if ln is not None and ln not in ["bn", "en"]:
        logger.error("[ytdebunk] Invalid language code. Valid options: [bn, en]")
        return None, None
    
    if st is not None and et is not None and st >= et:
        logger.error("[ytdebunk] Start time must be less than end time.")
        return None, None

    os.makedirs(settings.OUTPUT_DIRECTORY, exist_ok=True)

    # Subtitle-First Ingestion: Probe for existing subtitles unless --force_asr is requested
    subtitles_result = None
    if not args.force_asr:
        subtitles_result = extract_subtitles(
            args.yt_video_url,
            language=ln,
            start_time=st,
            end_time=et,
            verbose=args.verbose,
            ignore_ssl_cert=args.ignore_ssl,
            logger=logger
        )

    if subtitles_result is not None:
        segments, transcription = subtitles_result
        logger.info(f"[ytdebunk] Subtitles extracted successfully ({len(segments)} segments). Bypassing Whisper ASR (saved ~95% processing time).")
        try:
            with open(settings.SUBTITLES_JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(segments, f, ensure_ascii=False, indent=2)
        except Exception as e:
            if args.verbose:
                logger.warning(f"[ytdebunk] Could not write subtitles JSON: {e}")
    else:
        if not args.force_asr and args.verbose:
            logger.info("[ytdebunk] No matching subtitles found. Proceeding with audio download and Whisper ASR...")
        download_audio(args.yt_video_url, 
                       start_time=st, 
                       end_time=et, 
                       verbose=args.verbose, 
                       ignore_ssl_cert=args.ignore_ssl,
                       logger=logger)

        transcription = transcribe_audio(verbose=args.verbose, 
                                         start_time=st, 
                                         end_time=et,
                                         language=ln,
                                         key=token,
                                         logger=logger)
    
    with open(settings.TRANSCRIPTION_FILE, "w", encoding="utf-8") as f:
        f.write(transcription)
        if args.verbose:
            logger.info(f"[ytdebunk] Transcription saved at {settings.TRANSCRIPTION_FILE}")

    if args.enhance:
        transcription = enhance_transcription(transcription, 
                                              key=token, 
                                              verbose=args.verbose, 
                                              language=ln,
                                              logger=logger)
        
        with open(settings.REFINED_TRANSCRIPTION_FILE, "w", encoding="utf-8") as f:
            f.write(transcription)
            if args.verbose:
                logger.info(f"[ytdebunk] Refined transcription saved at {settings.REFINED_TRANSCRIPTION_FILE}")

    logical_faults = None
    
    if args.detect:
        logical_faults = detect_logical_faults(transcription, 
                                               key=token, 
                                               verbose=args.verbose, 
                                               language=ln, 
                                               logger=logger)
        
        with open(settings.LOGICAL_FAULTS_FILE, "w", encoding="utf-8") as f:
            f.write(logical_faults)
            if args.verbose:
                logger.info(f"[ytdebunk] Logical faults saved at {settings.LOGICAL_FAULTS_FILE}")

    report = None
    if args.verify or args.script or args.voice or args.sync or args.make_video:
        if token:
            report = verify_claims(
                transcription=transcription,
                key=token,
                language=ln,
                video_url=args.yt_video_url,
                verbose=args.verbose,
                logger=logger
            )
            with open(settings.DEBUNK_REPORT_JSON, "w", encoding="utf-8") as f:
                f.write(report.to_json())
            with open(settings.DEBUNK_REPORT_MD, "w", encoding="utf-8") as f:
                f.write(report.to_markdown())
            if args.verbose:
                logger.info(f"[ytdebunk] Debunk report saved at {settings.DEBUNK_REPORT_JSON} and {settings.DEBUNK_REPORT_MD}")

    script = None
    if (args.script or args.voice or args.sync or args.make_video) and report:
        script = generate_debunk_script(
            report=report,
            persona=args.persona,
            key=token,
            language=ln,
            verbose=args.verbose,
            logger=logger
        )
        if args.verbose:
            logger.info(f"[ytdebunk] Debunker script saved at {settings.DEBUNK_SCRIPT_JSON} and {settings.DEBUNK_SCRIPT_MD}")

    if (args.voice or args.make_video) and script:
        script = synthesize_script(
            script=script,
            voice=args.voice_name,
            gender=args.voice_gender,
            verbose=args.verbose,
            logger=logger
        )
        if args.verbose:
            logger.info(f"[ytdebunk] Voiceover audio synthesized at {script.audio_path}")

    timeline = None
    if (args.sync or args.make_video) and report and script:
        timeline = sync_timeline(
            report=report,
            script=script,
            mode="interleaved",
            verbose=args.verbose,
            logger=logger
        )
        if args.verbose:
            logger.info(f"[ytdebunk] Synchronized timeline saved at {settings.TIMELINE_JSON} and {settings.TIMELINE_MD}")

    video_path = None
    if args.make_video and report and script and timeline:
        src_video = getattr(settings, 'VIDEO_FILE', None)
        valid_src = src_video if (src_video and os.path.exists(src_video)) else None

        # Ensure source audio exists for claim excerpts if subtitles were used
        if not os.path.exists(settings.AUDIO_FILE):
            if args.verbose:
                logger.info("[ytdebunk] Source audio not found locally; downloading for video statement excerpts...")
            try:
                download_audio(
                    args.yt_video_url,
                    start_time=st,
                    end_time=et,
                    verbose=args.verbose,
                    ignore_ssl_cert=args.ignore_ssl,
                    logger=logger
                )
            except Exception as e_dl:
                if args.verbose:
                    logger.warning(f"[ytdebunk] Could not download audio for statement excerpts: {e_dl}")

        video_path = compose_debunk_video(
            report=report,
            script=script,
            timeline=timeline,
            aspect_ratio=args.aspect_ratio,
            source_video_path=valid_src,
            source_audio_path=settings.AUDIO_FILE if os.path.exists(settings.AUDIO_FILE) else None,
            verbose=args.verbose,
            logger=logger
        )
        if args.verbose:
            logger.info(f"[ytdebunk] Debunk video rendered at {video_path}")

    if args.verbose:
        logger.info("*" * 80)
        logger.info(f"[ytdebunk] TRANSCRIPTION:\n{transcription}")
        if args.enhance:
            logger.info("-" * 80)
            logger.info(f"[ytdebunk] REFINED TRANSCRIPTION:\n{transcription}")
        if args.detect:
            logger.info("-" * 80)
            logger.info(f"[ytdebunk] LOGICAL FAULTS:\n{logical_faults}")
        if report:
            logger.info("-" * 80)
            logger.info(f"[ytdebunk] DEBUNK REPORT (Score: {report.overall_veracity_score}%):\n{report.to_markdown()}")
        if script:
            logger.info("-" * 80)
            logger.info(f"[ytdebunk] DEBUNKER SCRIPT ({script.persona.upper()}):\n{script.to_markdown()}")
        if timeline:
            logger.info("-" * 80)
            logger.info(f"[ytdebunk] TIMELINE SHEET ({len(timeline.events)} events, {timeline.total_duration_seconds:.1f}s):\n{timeline.to_markdown()}")
        if video_path:
            logger.info("-" * 80)
            logger.info(f"[ytdebunk] DEBUNK VIDEO RENDERED:\n{video_path}")
        logger.info("*" * 80)

    return DebunkResult(transcription, logical_faults, report=report, script=script, timeline=timeline, video_path=video_path)

if __name__ == "__main__":
    main()
