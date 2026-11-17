import streamlit as st
from ytdebunk.ytdebunk import main as ytdebunk_main
import sys
import os
import logging
import ssl
import re
import yt_dlp

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
    """
    Extract YouTube thumbnail URL reliably without pytube.
    First tries regex extraction of YouTube video ID for instant zero-latency resolution.
    Falls back to yt-dlp metadata extraction.
    """
    if not video_url:
        return None
    try:
        match = re.search(r'(?:v=|\/|youtu\.be\/|shorts\/)([0-9A-Za-z_-]{11})', video_url)
        if match:
            video_id = match.group(1)
            return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'extract_flat': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            if info:
                if info.get('thumbnail'):
                    return info['thumbnail']
                thumbnails = info.get('thumbnails', [])
                if thumbnails:
                    return thumbnails[-1].get('url')
    except Exception:
        return None
    return None

def run_ytdebunk(
    video_url,
    st_time,
    et_time,
    language,
    enhance,
    detect,
    verbose,
    token,
    log_placeholder,
    verify=False,
    script=False,
    persona="skeptic",
    voice=False,
    voice_name=None,
    sync=False,
    make_video=False,
    aspect_ratio="landscape",
    force_asr=False
):
    args = [video_url]

    if st_time is not None:
        args.extend(['--start_time', str(st_time)])
    if et_time is not None:
        args.extend(['--end_time', str(et_time)])

    if enhance:
        args.append('--enhance')
    if detect:
        args.append('--detect')
    if verify:
        args.append('--verify')
    if script:
        args.append('--script')
        args.extend(['--persona', persona])
    if voice:
        args.append('--voice')
        if voice_name:
            args.extend(['--voice_name', voice_name])
    if sync:
        args.append('--sync')
    if make_video:
        args.append('--make_video')
        args.extend(['--aspect_ratio', aspect_ratio])
    if force_asr:
        args.append('--force_asr')
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

    args.extend(['--ignore_ssl'])
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    streamlit_handler = StreamlitLogger(log_placeholder)
    logger.addHandler(streamlit_handler)

    sys.argv = ['ytdebunk'] + args
    result = ytdebunk_main()

    if result is None:
        return None, None, None, None, None, None

    report = getattr(result, 'report', None)
    debunk_script = getattr(result, 'script', None)
    timeline = getattr(result, 'timeline', None)
    video_path = getattr(result, 'video_path', None)
    transcription = result[0] if len(result) > 0 else None
    logical_faults = result[1] if len(result) > 1 else None

    return transcription, logical_faults, report, debunk_script, timeline, video_path

def main():
    st.set_page_config(page_title="AI Debunker Studio", page_icon="🕵️", layout="wide")
    st.title("🕵️ AI Debunker Studio (ytdebunk 2.0)")
    st.info("Autonomous, zero-cost AI Debunker Studio: Probes captions, verifies claims with live web grounding, generates persona-driven scripts, synthesizes neural voiceover (Edge-TTS), and synchronizes audio-claim timelines.")
    
    col_input, col_config = st.columns([2, 1])

    with col_input:
        video_url = st.text_input("YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
        col_st, col_et = st.columns(2)
        with col_st:
            st_time_input = st.text_input("Start Time (in seconds, optional)")
        with col_et:
            et_time_input = st.text_input("End Time (in seconds, optional)")

    with col_config:
        language = st.selectbox("Language", ["English", "Bengali"])
        verify = st.checkbox("🔍 Verify Claims & Live Web Grounding", value=True, help="Extracts claims and fact-checks via DuckDuckGo + Gemini Search Grounding")
        
        gen_script = st.checkbox("🎭 Generate Debunker Script", value=True, help="Drafts a spoken script for a virtual debunker character")
        persona_choice = "skeptic"
        if gen_script:
            persona_label = st.selectbox(
                "Debunker Persona",
                ["The Witty Skeptic (Engaging & Punchy)", "The Analytical Journalist (Rigorous & Fact-Driven)", "The Educational Mentor (Patient & Pedagogical)"]
            )
            if "Skeptic" in persona_label:
                persona_choice = "skeptic"
            elif "Journalist" in persona_label:
                persona_choice = "journalist"
            else:
                persona_choice = "educator"

        gen_voice = st.checkbox("🎙️ Synthesize Neural Voiceover (Edge-TTS)", value=False, help="Zero-cost neural TTS voice synthesis via Microsoft Edge TTS")
        voice_selected = None
        if gen_voice:
            if language == "Bengali":
                voice_options = [
                    "bn-BD-PradeepNeural (Male - BD)",
                    "bn-BD-NabanitaNeural (Female - BD)",
                    "bn-IN-BashkarNeural (Male - IN)",
                    "bn-IN-TanishaaNeural (Female - IN)"
                ]
            else:
                voice_options = [
                    "en-US-GuyNeural (Male - US)",
                    "en-US-JennyNeural (Female - US)",
                    "en-US-ChristopherNeural (Male - US)",
                    "en-US-AvaNeural (Female - US)"
                ]
            v_choice = st.selectbox("Neural Voice", voice_options)
            voice_selected = v_choice.split(" ")[0]

        gen_sync = st.checkbox("⏱️ Synchronize Timeline Cue Sheet", value=True, help="Calculates audio-claim sync intervals for video composition")
        gen_video = st.checkbox("🎬 Render Debunk Video (MP4)", value=False, help="Renders an MP4 debunk video combining visual cards, claim excerpts, and synthesized neural voiceover")
        aspect_ratio = "landscape"
        if gen_video:
            layout_choice = st.selectbox("Video Layout", ["Landscape (16:9, YouTube)", "Vertical (9:16, Shorts / TikTok)"])
            aspect_ratio = "vertical" if "Vertical" in layout_choice else "landscape"

        detect = st.checkbox("🧠 Detect Logical Fallacies", value=True)
        enhance = st.checkbox("✨ Enhance Transcription (LLM)", value=False)
        force_asr = st.checkbox("⚙️ Force Whisper ASR (Skip Captions)", value=False, help="Probes YouTube captions first to save ~95% processing time.")
        verbose = st.checkbox("📝 Verbose Output", value=True)
        token = st.text_input("Gemini API Key (optional if GEMINI_API_KEY env set)", type="password")

    try:
        st_time = int(st_time_input) if st_time_input else None
        et_time = int(et_time_input) if et_time_input else None
    except ValueError:
        st.error("Please enter valid integers for start and end times.")
        return

    log_placeholder = st.empty()

    if st.button("🚀 Analyze & Debunk Video", use_container_width=True):
        if not video_url:
            st.error("Please provide a valid YouTube video URL.")
            return

        preview_col, info_col = st.columns([1, 1])
        with preview_col:
            video_preview = get_video_preview(video_url)
            if video_preview:
                st.image(video_preview, caption="Video Preview", use_container_width=True)
        with info_col:
            st.video(video_url)

        with st.spinner('Deconstructing claims, generating persona script, and synthesizing voiceover...'):
            transcription, fallacies, report, script, timeline = run_ytdebunk(
                video_url=video_url,
                st_time=st_time,
                et_time=et_time,
                language=language,
                enhance=enhance,
                detect=detect,
                verbose=verbose,
                token=token,
                log_placeholder=log_placeholder,
                verify=verify,
                script=gen_script,
                persona=persona_choice,
                voice=gen_voice,
                voice_name=voice_selected,
                sync=gen_sync,
                make_video=gen_video,
                aspect_ratio=aspect_ratio,
                force_asr=force_asr
            )

            if transcription:
                st.success("Analysis and studio synthesis complete!")
                
                # Tabbed presentation
                tabs = []
                if video_path and os.path.exists(video_path):
                    tabs.append("🎬 Debunk Video")
                if report:
                    tabs.append("📊 Debunk Report")
                if script:
                    tabs.append("🎭 Debunker Script")
                if timeline:
                    tabs.append("⏱️ Audio-Claim Timeline")
                tabs.append("📜 Transcript")
                if detect and fallacies:
                    tabs.append("🧠 Logical Fallacies")

                tab_objects = st.tabs(tabs)
                curr_tab = 0

                # Tab 0: Rendered Video
                if video_path and os.path.exists(video_path):
                    with tab_objects[curr_tab]:
                        st.subheader("🎬 Rendered Debunk Video")
                        st.video(video_path)
                        with open(video_path, "rb") as vf:
                            video_bytes = vf.read()
                        st.download_button(
                            "📥 Download Rendered Debunk Video (.mp4)",
                            data=video_bytes,
                            file_name=os.path.basename(video_path),
                            mime="video/mp4"
                        )
                    curr_tab += 1

                # Tab 1: Debunk Report
                if report:
                    with tab_objects[curr_tab]:
                        st.metric("Overall Veracity Score", f"{report.overall_veracity_score:.1f}%")
                        st.progress(max(0.0, min(1.0, report.overall_veracity_score / 100.0)))
                        
                        st.subheader("Executive Summary")
                        st.markdown(report.summary)

                        if report.fallacies_found:
                            st.warning(f"**Identified Fallacies:** {', '.join(report.fallacies_found)}")

                        if report.claims:
                            st.subheader("Deconstructed Claims & Grounded Verification")
                            for c in report.claims:
                                with st.expander(f"Claim #{c.id}: {c.claim_text} ({c.veracity})", expanded=True):
                                    st.markdown(f"**Original Quote:** *\"{c.original_quote}\"*")
                                    st.markdown(f"**Veracity Assessment:** `{c.veracity}` (Confidence: {int(c.confidence_score * 100)}%)")
                                    st.markdown(f"**Claim Type:** `{c.claim_type}`")
                                    if c.is_fallacious and c.fallacy_type:
                                        st.error(f"**Logical Fallacy:** {c.fallacy_type} — {c.fallacy_explanation}")
                                    st.markdown(f"**Evidence & Grounding:** {c.evidence_summary}")
                                    if c.sources:
                                        st.markdown("**Authoritative Sources:**")
                                        for s in c.sources:
                                            st.markdown(f"- [{s}]({s})")
                                    if c.counter_argument:
                                        st.info(f"**Counter-Argument Rebuttal:** {c.counter_argument}")

                        dl_col1, dl_col2 = st.columns(2)
                        with dl_col1:
                            st.download_button(
                                "📥 Download Debunk Report (.md)",
                                data=report.to_markdown(),
                                file_name="debunk_report.md",
                                mime="text/markdown"
                            )
                        with dl_col2:
                            st.download_button(
                                "📥 Download Structured Data (.json)",
                                data=report.to_json(),
                                file_name="debunk_report.json",
                                mime="application/json"
                            )
                    curr_tab += 1

                # Tab 2: Debunker Script
                if script:
                    with tab_objects[curr_tab]:
                        st.subheader(f"Debunker Script: Persona '{script.persona.capitalize()}'")
                        if script.total_duration_seconds:
                            st.info(f"⏱️ **Synthesized Audio Duration:** `{script.total_duration_seconds:.1f}s`")

                        if script.audio_path and os.path.exists(script.audio_path):
                            st.markdown("#### 🎙️ Complete Debunker Voiceover Audio")
                            st.audio(script.audio_path)

                        st.markdown("#### 🎙️ Hook (Opening)")
                        st.info(script.hook)

                        st.markdown("#### 🎬 Rebuttal Segments")
                        for seg in script.segments:
                            with st.container():
                                st.markdown(f"**Segment #{seg.segment_id} (Claim #{seg.claim_id or 'General'})**")
                                if seg.speaker_quote:
                                    st.caption(f"Target Quote: \"{seg.speaker_quote}\"")
                                if seg.visual_cue:
                                    st.markdown(f"*Visual Cue:* `{seg.visual_cue}`")
                                st.write(seg.rebuttal_text)
                                if seg.audio_path and os.path.exists(seg.audio_path):
                                    st.audio(seg.audio_path)
                                st.divider()

                        st.markdown("#### 🏁 Outro (Closing)")
                        st.info(script.outro)

                        sdl_col1, sdl_col2 = st.columns(2)
                        with sdl_col1:
                            st.download_button(
                                "📥 Download Script (.md)",
                                data=script.to_markdown(),
                                file_name="debunk_script.md",
                                mime="text/markdown"
                            )
                        with sdl_col2:
                            st.download_button(
                                "📥 Download Script Data (.json)",
                                data=script.to_json(),
                                file_name="debunk_script.json",
                                mime="application/json"
                            )
                    curr_tab += 1

                # Tab 3: Timeline Sheet
                if timeline:
                    with tab_objects[curr_tab]:
                        st.subheader("⏱️ Synchronized Audio-Claim Video Timeline")
                        st.metric("Total Video Runtime", f"{timeline.total_duration_seconds:.1f}s")
                        
                        # Markdown table overview
                        st.markdown(timeline.to_markdown())

                        tdl_col1, tdl_col2 = st.columns(2)
                        with tdl_col1:
                            st.download_button(
                                "📥 Download Timeline (.md)",
                                data=timeline.to_markdown(),
                                file_name="timeline.md",
                                mime="text/markdown"
                            )
                        with tdl_col2:
                            st.download_button(
                                "📥 Download Timeline Data (.json)",
                                data=timeline.to_json(),
                                file_name="timeline.json",
                                mime="application/json"
                            )
                    curr_tab += 1

                # Tab 4: Transcript
                with tab_objects[curr_tab]:
                    st.text_area("Video Transcript", transcription, height=300)
                curr_tab += 1

                # Tab 5: Fallacies
                if detect and fallacies and curr_tab < len(tab_objects):
                    with tab_objects[curr_tab]:
                        st.text_area("Logical Faults Assessment", fallacies, height=300)
            else:
                st.error("Failed to generate transcription or analysis. Check the logs for details.")

if __name__ == "__main__":
    main()
