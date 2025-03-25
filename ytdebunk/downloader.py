import os
import yt_dlp
import ytdebunk.settings as settings

def download_audio(video_url, start_time=None, end_time=None, verbose=False, ignore_ssl_cert=True):
    if verbose:
        print(f"[ytdebunk-download] Downloading audio from {video_url}...")

    os.makedirs(settings.OUTPUT_DIRECTORY, exist_ok=True)

    if os.path.exists(settings.AUDIO_FILE):
        os.remove(settings.AUDIO_FILE)

    postprocessor_args = []
    if start_time is not None or end_time is not None:
        postprocessor_args = ["-ss", str(start_time)] if start_time is not None else []
        if end_time is not None:
            postprocessor_args += ["-to", str(end_time)]

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'postprocessor_args': postprocessor_args,
        'outtmpl': os.path.splitext(settings.AUDIO_FILE)[0],
        'noplaylist': True,
        'progress_hooks': [lambda d: print(f" Downloading: {d.get('_percent_str', '0%')} complete")],
        'cachedir': False,
        'quiet': not verbose,
        'nocheckcertificate': ignore_ssl_cert,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
        if verbose:
            print(f"[ytdebunk-download] Audio download complete! Saved at {settings.AUDIO_FILE}")
