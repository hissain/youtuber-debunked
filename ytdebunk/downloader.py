import os, sys
import yt_dlp
import ytdebunk.settings as settings
import logging

def download_audio(video_url, start_time=None, end_time=None, verbose=False, ignore_ssl_cert=False, logger=None):
    
    if logger is None:
        logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
        logger = logging.getLogger(__name__)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

    if verbose:
        logger.info(f"[ytdebunk-download] Downloading audio from {video_url}...")

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
            logger.info(f"[ytdebunk-download] Audio download complete! Saved at {settings.AUDIO_FILE}")

def download_video(video_url, output_path=None, start_time=None, end_time=None, verbose=False, ignore_ssl_cert=False, logger=None):
    """
    Downloads source video (MP4) sliced to start_time / end_time if requested.
    Used by the video compositor to extract high-fidelity video excerpts of claims.
    """
    if logger is None:
        logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
        logger = logging.getLogger(__name__)

    os.makedirs(settings.OUTPUT_DIRECTORY, exist_ok=True)
    out_file = output_path or settings.VIDEO_FILE
    if os.path.exists(out_file):
        try:
            os.remove(out_file)
        except Exception:
            pass

    postprocessor_args = []
    if start_time is not None or end_time is not None:
        postprocessor_args = ["-ss", str(start_time)] if start_time is not None else []
        if end_time is not None:
            postprocessor_args += ["-to", str(end_time)]

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.splitext(out_file)[0] + '.%(ext)s',
        'noplaylist': True,
        'cachedir': False,
        'quiet': not verbose,
        'nocheckcertificate': ignore_ssl_cert,
    }
    if postprocessor_args:
        ydl_opts['postprocessor_args'] = postprocessor_args

    if verbose:
        logger.info(f"[ytdebunk-download] Downloading video from {video_url} to {out_file}...")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    # If yt-dlp appended an extension, normalize to out_file
    base_no_ext = os.path.splitext(out_file)[0]
    for ext in ['.mp4', '.mkv', '.webm']:
        cand = base_no_ext + ext
        if os.path.exists(cand) and cand != out_file:
            try:
                if os.path.exists(out_file):
                    os.remove(out_file)
                os.rename(cand, out_file)
                break
            except Exception:
                return cand

    if verbose:
        logger.info(f"[ytdebunk-download] Video download complete! Saved at {out_file}")

    return out_file

if __name__ == "__main__":
    download_audio("https://www.youtube.com/shorts/l8UDM4bOhpU", verbose=True)