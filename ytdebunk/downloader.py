import os
import yt_dlp

def download_audio(video_url, output_dir="downloads", output_audio="audio.mp3"):
    os.makedirs(output_dir, exist_ok=True)
    os.remove(os.path.join(output_dir, output_audio)) if os.path.exists(os.path.join(output_dir, output_audio)) else None
    
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
        'cachedir': False,  # Disable caching, as we're not going to download the same video again
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    
    print(f"Audio download complete! Saved at {os.path.join(output_dir, output_audio)}")
