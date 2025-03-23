import os
import argparse
import yt_dlp

def download_audio(video_url, output_dir="downloads", output_audio="audio.mp3"):
    """
    Downloads audio from a YouTube video and saves it as an MP3 file.
    :param video_url: URL of the YouTube video
    :param output_dir: Directory to save the downloaded file
    :param output_audio: Name of the output audio file (MP3 format)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',  # Select best audio format
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',  # Extract audio using FFmpeg
            'preferredcodec': 'mp3',      # Convert to MP3
            'preferredquality': '192',    # Set quality (kbps)
        }],
        'outtmpl': os.path.join(output_dir, os.path.splitext(output_audio)[0]),
        'noplaylist': True,  # Download a single video, not a playlist
        'progress_hooks': [lambda d: print(f"Downloading: {d.get('_percent_str', '0%')} complete")],
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    
    print(f"Audio download complete! Saved at {os.path.join(output_dir, output_audio)}")
