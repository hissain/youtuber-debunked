import streamlit as st
from ytdebunk.ytdebunk import main as ytdebunk_main
import sys

def run_ytdebunk(video_url, enhance, detect, verbose, token):

    args = [video_url]
    if enhance:
        args.append('--enhance')
    if detect:
        args.extend(['--detect'])
    if verbose:
        args.append('--verbose')
    if token:
        args.extend(['--token', token])

    sys.argv = ['ytdebunk'] + args
    return ytdebunk_main()

def main():
    st.title("Bangla YouTube Debunking Tool")

    video_url = st.text_input("YouTube Video URL")
    enhance = st.checkbox("Enhance Transcription")
    detect = st.checkbox("Detect Logical Fallacies")
    verbose = st.checkbox("Verbose Output")
    token = st.text_input("Gemini API Token", type="password")

    if st.button("Transcribe and Debunk This Video"):
        with st.spinner('Processing...'):
            transcription, fallacies = run_ytdebunk(video_url, enhance, detect, verbose, token)
            
            if transcription:
                st.success("ytdebunk has been executed successfully.")
                st.text_area("Video Transcription", transcription, height=200)
            else:
                st.error("Failed to generate transcription. Please check the logs for more details.")

            if fallacies:
                st.text_area("Appearant Logical Faults:", fallacies, height=300)
            else:
                st.error("Failed to generate logical faults. Please check the logs for more details.")    

if __name__ == "__main__":
    main()