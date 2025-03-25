import argparse
import os
import ytdebunk.settings as settings
from dotenv import load_dotenv
from ytdebunk.downloader import download_audio
from ytdebunk.transcriber import transcribe_audio
from ytdebunk.refiner import enhance_transcription
from ytdebunk.philosopher import detect_logical_faults


load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Download audio from a YouTube video.")
    parser.add_argument("yt_video_url", type=str, help="URL of the YouTube video")
    parser.add_argument("-e", "--enhance", action="store_true", help="Enhance the transcription")
    parser.add_argument("-d", "--detect", action="store_true", help="Detect logical fallacies, bias, irony, faults in the transcription")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    parser.add_argument("-t", "--token", type=str, help="API token for the Gemini API")
    parser.add_argument("-st", "--start_time", type=float, default=None, help="Start time of the audio clip in seconds")
    parser.add_argument("-et", "--end_time", type=float, default=None, help="End time of the audio clip in seconds")
    parser.add_argument("-m", "--model", type=str, default=settings.TRANSCRIPTION_MODEL, help="Path to the transcription (WhisperFeatureExtractor) model")
    parser.add_argument("-is", "--ignore_ssl", action="store_true", default=True, help="Ignore SSL certificate errors (nocheckcertificate)")
    # parser.add_argument("-debug", "--debug", action="store_true", help="Used for debugging purpose")
    
    args = parser.parse_args()

    if args.enhance:
        token = args.token or os.getenv("GEMINI_API_TOKEN") or os.getenv("GEMINI_API_KEY")
        if not token:
            print("[ytdebunk] Error: Enhancement is enabled but no Gemini API token provided or found in env.")
            return

    st = args.start_time
    et = args.end_time
    
    if st is not None and et is not None and st >= et:
        print("[ytdebunk] Error: Start time must be less than end time.")
        return
    
    download_audio(args.yt_video_url, start_time=st, end_time=et, verbose=args.verbose)
    transcription = transcribe_audio(verbose=args.verbose, start_time=st, end_time=et, model_path=args.model)
    
    with open(settings.TRANSCRIPTION_FILE, "w", encoding="utf-8") as f:
            f.write(transcription)
            if args.verbose:
                print(f"[ytdebunk] Transcription saved at {settings.TRANSCRIPTION_FILE}")

    if args.enhance:
        transcription = enhance_transcription(transcription, token, verbose=args.verbose)
        with open(settings.REFINED_TRANSCRIPTION_FILE, "w", encoding="utf-8") as f:
            f.write(transcription)
            if args.verbose:
                print(f"[ytdebunk] Refined transcription saved at {settings.REFINED_TRANSCRIPTION_FILE}")

    logical_faults = detect_logical_faults(transcription, verbose=args.verbose)
    
    with open(settings.LOGICAL_FAULTS_FILE, "w", encoding="utf-8") as f:
        f.write(logical_faults)
        if args.verbose:
            print(f"[ytdebunk] Logical faults saved at {settings.LOGICAL_FAULTS_FILE}")
    
    if args.verbose:
        print(f"*"*80)
        print(f"[ytdebunk] TRANSCRIPTION:\n{transcription}")
        print(f"-"*80)
        print(f"[ytdebunk] REFINED TRANSCRIPTION:\n{transcription}")
        print(f"-"*80)
        print(f"[ytdebunk] LOGICAL FAULTS:\n{logical_faults}")
        print(f"*"*80)

    return transcription, logical_faults
