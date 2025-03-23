import os
import argparse
from downloader import download_audio
from transcribe import transcribe_audio

def main():
    parser = argparse.ArgumentParser(description="Download audio from a YouTube video.")
    parser.add_argument("video_url", type=str, help="URL of the YouTube video")
    args = parser.parse_args()
    download_audio(args.video_url)
    transcribe_audio()

if __name__ == "__main__":
    main()