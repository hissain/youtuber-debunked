import argparse
import os
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
    parser.add_argument("-o", "--output_file", type=str, default="downloads/transcription.txt", help="Path to save the final transcription")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    parser.add_argument("-t", "--token", type=str, help="API token for the Gemini API")
    # parser.add_argument("-debug", "--debug", action="store_true", help="Used for debugging purpose")
    
    args = parser.parse_args()

    if args.enhance:
        token = args.token or os.getenv("GEMINI_API_TOKEN") or os.getenv("GEMINI_API_KEY")
        if not token:
            print("Error: Enhancement is enabled but no Gemini API token provided or found in env.")
            return

    download_audio(args.yt_video_url)
    transcription = transcribe_audio()

    if args.enhance:
        refined_transcription = enhance_transcription(transcription, token)
    else:
        refined_transcription = transcription

    with open(args.output_file, "w", encoding="utf-8") as f:
        f.write(refined_transcription)

    fallacies = detect_logical_faults(refined_transcription)
    
    with open("downloads/fallacies.txt", "w", encoding="utf-8") as f:
        f.write(fallacies)
    
    print("Transcription saved to", args.output_file)
    if args.verbose:
        print(f"Refined transcription:\n{refined_transcription}")
        print(f"Logical faults:\n{fallacies}")
