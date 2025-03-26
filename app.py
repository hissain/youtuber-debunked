import streamlit as st
from ytdebunk.ytdebunk import main as ytdebunk_main
import sys
import logging

class StreamlitLogger(logging.StreamHandler):
    def __init__(self, placeholder):
        super().__init__()
        self.placeholder = placeholder
        self.log_messages = []

    def emit(self, record):
        log_entry = self.format(record)
        self.log_messages.append(log_entry)
        self.placeholder.text("\n".join(self.log_messages))

def run_ytdebunk(video_url, language, enhance, detect, verbose, token, log_placeholder):

    args = [video_url]
    if enhance:
        args.append('--enhance')
    if detect:
        args.extend(['--detect'])
    if verbose:
        args.append('--verbose')
    if token:
        args.extend(['--token', token])
    if language == "Bengali":
        args.append('--language')
        args.append('bn')

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    streamlit_handler = StreamlitLogger(log_placeholder)
    logger.addHandler(streamlit_handler)

    sys.argv = ['ytdebunk'] + args
    return ytdebunk_main()

def main():
    st.title("YouTuber Debunking Tool")

    video_url = st.text_input("YouTube Video URL")
    language = st.selectbox("Language", ["English", "Bengali"])
    enhance = st.checkbox("Enhance Transcription")
    detect = st.checkbox("Detect Logical Fallacies")
    verbose = st.checkbox("Verbose Output")
    token = st.text_input("Gemini API Token", type="password")

    log_placeholder = st.empty()

    if st.button("Transcribe and Debunk This Video"):
        with st.spinner('Processing...'):
            transcription, fallacies = run_ytdebunk(video_url, language, enhance, detect, verbose, token, log_placeholder)
            
            if transcription:
                st.success("ytdebunk has been executed successfully.")
                st.text_area("Video Transcription", transcription, height=200)
            else:
                st.error("Failed to generate transcription. Please check the logs for more details.")

            if detect:
                if fallacies:
                    st.text_area("Apparent Logical Faults in the Transcription:", fallacies, height=300)
                else:
                    st.error("Failed to generate logical faults. Please check the logs for more details.")    

if __name__ == "__main__":
    main()