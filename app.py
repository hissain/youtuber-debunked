import streamlit as st
from ytdebunk.ytdebunk import main as ytdebunk_main
import sys
import logging
import ssl
import pytube

ssl._create_default_https_context = ssl._create_unverified_context

class StreamlitLogger(logging.StreamHandler):
    def __init__(self, placeholder):
        super().__init__()
        self.placeholder = placeholder
        self.log_messages = []

    def emit(self, record):
        log_entry = self.format(record)
        self.log_messages.append(log_entry)
        log_text = "\n".join(self.log_messages)
        self.placeholder.markdown(f"#### Logs\n\n```text\n{log_text}\n```")

def get_video_preview(video_url):
    try:
        yt = pytube.YouTube(video_url)
        return yt.thumbnail_url
    except Exception as e:
        return None

def run_ytdebunk(video_url, st_time, et_time, language, enhance, detect, verbose, token, log_placeholder):

    args = [video_url]

    if st_time is not None:
        args.extend(['--start_time', str(st_time)])
    if et_time is not None:
        args.extend(['--end_time', str(et_time)])

    if enhance:
        args.append('--enhance')
    if detect:
        args.append('--detect')
    if verbose:
        args.append('--verbose')
    if token:
        args.extend(['--token', token])
    
    if language == "Bengali":
        args.extend(['--language', 'bn'])
    elif language == "English":
        args.extend(['--language', 'en'])
    else:
        args.extend(['--language', 'en'])

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    streamlit_handler = StreamlitLogger(log_placeholder)
    logger.addHandler(streamlit_handler)

    sys.argv = ['ytdebunk'] + args
    result = ytdebunk_main()

    if result is None:
        return None, None
    elif result[1] is None:
        return result[0], None
    return result

def main():
    st.title("YouTuber Debunking Tool")
    st.info("This tool transcribes YouTube videos and detects logical fallacies in the transcription using AI.")
    st.markdown("### Instructions\n1. Paste the YouTube video URL in the input box below.\n2. Select the language of the video.\n3. Check the boxes to enhance the transcription and detect logical fallacies.\n4. Enter your Gemini API token if you want to enhance the transcription.\n5. Click the button to start the process.\n6. The transcription and logical fallacies will be displayed below.")

    video_url = st.text_input("YouTube Video URL")
    language = st.selectbox("Language", ["English", "Bengali"])
    st_time_input = st.text_input("Start Time (in seconds)")
    et_time_input = st.text_input("End Time (in seconds)")
    enhance = st.checkbox("Enhance Transcription")
    detect = st.checkbox("Detect Logical Fallacies")
    verbose = st.checkbox("Verbose Output")
    token = st.text_input("Gemini API Token", type="password")

    try:
        st_time = int(st_time_input) if st_time_input else None
        et_time = int(et_time_input) if et_time_input else None
    except ValueError:
        st.error("Please enter valid integers for start and end times.")
        return

    log_placeholder = st.empty()

    if st.button("Transcribe and Debunk This Video"):
        if video_url:
            video_preview = get_video_preview(video_url)
            if video_preview:
                st.image(video_preview, caption="Video Preview", use_column_width=True)
            st.video(video_url)

        with st.spinner('Processing...'):
            transcription, fallacies = run_ytdebunk(video_url, st_time, et_time, language, enhance, detect, verbose, token, log_placeholder)
            
            if transcription:
                st.success("ytdebunk has been executed successfully.")
                st.text_area("Video Transcription", transcription, height=200)
            else:
                st.error("Failed to generate transcription. Please check the logs for more details.")

            if detect:
                if fallacies:
                    st.text_area("Apparent Logical Faults in the Transcription:", fallacies, height=300)  

if __name__ == "__main__":
    main()