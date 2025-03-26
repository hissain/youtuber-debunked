import argparse
import os
import sys
import logging
import ytdebunk.settings as settings
from dotenv import load_dotenv
from ytdebunk.downloader import download_audio
from ytdebunk.transcriber import transcribe_audio
from ytdebunk.refiner import enhance_transcription
from ytdebunk.philosopher import detect_logical_faults

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="This command aims to automate the extraction of MP3 audio from a given YouTube video link, transcribe the audio content, and analyze the transcriptions using Agentic AI to identify logical fallacies and incorrect claims made by YouTubers.")
    parser.add_argument("yt_video_url", type=str, help="URL of the YouTube video (shorts, video) to be analyzed")
    parser.add_argument("-l", "--language", type=str, default="en", help="Language (code) of the transcription. Valid: [bn, en], default: en")
    parser.add_argument("-e", "--enhance", action="store_true", default=False, help="Enhance the transcription")
    parser.add_argument("-d", "--detect", action="store_true", default=False, help="Detect logical fallacies, bias, irony, faults in the transcription")
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help="Increase output verbosity")
    parser.add_argument("-t", "--token", type=str, help="API token for the Gemini API")
    parser.add_argument("-st", "--start_time", type=int, default=None, help="Start time of the audio clip in seconds for trasncription")
    parser.add_argument("-et", "--end_time", type=int, default=None, help="End time of the audio clip in seconds for trasncription")
    parser.add_argument("-is", "--ignore_ssl", action="store_true", default=False, help="Ignore SSL certificate errors (nocheckcertificate)")
    # parser.add_argument("-debug", "--debug", action="store_true", help="Used for debugging purpose")
    
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    logger = logging.getLogger(__name__)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    if args.verbose:
        logger.info(f"[ytdebunk] Analyzing YouTube video: {args.yt_video_url}")
        logger.info(f"[ytdebunk] Language: {args.language}")
        logger.info(f"[ytdebunk] Enhance: {args.enhance}")
        logger.info(f"[ytdebunk] Detect: {args.detect}")
        logger.info(f"[ytdebunk] Start Time: {args.start_time}")
        logger.info(f"[ytdebunk] End Time: {args.end_time}")
        logger.info(f"[ytdebunk] Ignore SSL: {args.ignore_ssl}")
        logger.info(f"[ytdebunk] Verbose: {args.verbose}")
        # logger.info(f"[ytdebunk] API Token: {args.token}")

    if args.token:
        logger.info(f"[ytdebunk] Using API token from argument instead of environment.")
    else:
        logger.info(f"[ytdebunk] No API token provided. Will use the token from environment.")
        if os.getenv("GEMINI_API_KEY"):
            logger.info(f"[ytdebunk] API token found in environment.")
        else:
            logger.info(f"[ytdebunk] No API token found in environment.")
            return None, None


    if args.enhance or args.detect:
        token = args.token or os.getenv("GEMINI_API_KEY")
        if not token:
            logger.error("[ytdebunk] Enhancement/Detection is enabled but no Gemini API token provided or found in env.")
            return None, None

    st = args.start_time
    et = args.end_time
    ln = args.language

    if ln is not None and ln not in ["bn", "en"]:
        logger.error("[ytdebunk] Invalid language. Valid: [bn, en]")
        return None, None
    
    if st is not None and et is not None and st >= et:
        logger.error("[ytdebunk] Start time must be less than end time.")
        return None, None
    
    download_audio(args.yt_video_url, 
                   start_time=st, 
                   end_time=et, 
                   verbose=args.verbose, 
                   ignore_ssl_cert=args.ignore_ssl,
                   logger=logger)

    transcription = transcribe_audio(verbose=args.verbose, 
                                     start_time=st, 
                                     end_time=et,
                                     language = ln,
                                     logger=logger)
    
    with open(settings.TRANSCRIPTION_FILE, "w", encoding="utf-8") as f:
            f.write(transcription)
            if args.verbose:
                logger.info(f"[ytdebunk] Transcription saved at {settings.TRANSCRIPTION_FILE}")

    if args.enhance:
        transcription = enhance_transcription(transcription, 
                                              token, 
                                              verbose=args.verbose, 
                                              language=ln,
                                              logger=logger)
        
        with open(settings.REFINED_TRANSCRIPTION_FILE, "w", encoding="utf-8") as f:
            f.write(transcription)
            if args.verbose:
                logger.info(f"[ytdebunk] Refined transcription saved at {settings.REFINED_TRANSCRIPTION_FILE}")

    logical_faults = detect_logical_faults(transcription, verbose=args.verbose, language=ln, logger=logger)
    
    with open(settings.LOGICAL_FAULTS_FILE, "w", encoding="utf-8") as f:
        f.write(logical_faults)
        if args.verbose:
            logger.info(f"[ytdebunk] Logical faults saved at {settings.LOGICAL_FAULTS_FILE}")
    
    if args.verbose:
        logger.info(f"*"*80)
        logger.info(f"[ytdebunk] TRANSCRIPTION:\n{transcription}")
        logger.info(f"-"*80)
        logger.info(f"[ytdebunk] REFINED TRANSCRIPTION:\n{transcription}")
        logger.info(f"-"*80)
        logger.info(f"[ytdebunk] LOGICAL FAULTS:\n{logical_faults}")
        logger.info(f"*"*80)

    return transcription, logical_faults
