OUTPUT_DIRECTORY = 'output'
AUDIO_FILE = OUTPUT_DIRECTORY + '/audio.mp3'
VIDEO_FILE = OUTPUT_DIRECTORY + '/video.mp4'
TRANSCRIPTION_FILE = OUTPUT_DIRECTORY + '/transcription.txt'
REFINED_TRANSCRIPTION_FILE = OUTPUT_DIRECTORY + '/refined_transcription.txt'
LOGICAL_FAULTS_FILE = OUTPUT_DIRECTORY + '/logical_faults.txt'
SUBTITLES_JSON_FILE = OUTPUT_DIRECTORY + '/subtitles.json'
DEBUNK_REPORT_JSON = OUTPUT_DIRECTORY + '/debunk_report.json'
DEBUNK_REPORT_MD = OUTPUT_DIRECTORY + '/debunk_report.md'
DEBUNK_SCRIPT_JSON = OUTPUT_DIRECTORY + '/debunk_script.json'
DEBUNK_SCRIPT_MD = OUTPUT_DIRECTORY + '/debunk_script.md'
TIMELINE_JSON = OUTPUT_DIRECTORY + '/timeline.json'
TIMELINE_MD = OUTPUT_DIRECTORY + '/timeline.md'
AUDIO_SEGMENTS_DIR = OUTPUT_DIRECTORY + '/audio_segments'
FULL_DEBUNK_AUDIO = OUTPUT_DIRECTORY + '/debunk_voiceover.mp3'
DEBUNK_VIDEO_FILE = OUTPUT_DIRECTORY + '/debunk_video.mp4'
DEBUNK_SHORTS_FILE = OUTPUT_DIRECTORY + '/debunk_shorts.mp4'
GRAPHICS_DIR = OUTPUT_DIRECTORY + '/graphics'

VIDEO_RESOLUTIONS = {
    "landscape": (1280, 720),
    "vertical": (720, 1280)
}

LANGUAGE_DEFAULT = "en"
LANUAGE_DEFAULT = "en"

DEFAULT_PERSONA = "skeptic"
PERSONAS = ["skeptic", "journalist", "educator"]

DEFAULT_VOICES = {
    "en": {
        "male": "en-US-GuyNeural",
        "female": "en-US-JennyNeural"
    },
    "bn": {
        "male": "bn-BD-PradeepNeural",
        "female": "bn-BD-NabanitaNeural"
    }
}

TRANSCRIPTION_MODELS = {
    "en": "openai/whisper-small",
    "bn": "bangla-speech-processing/BanglaASR"
}

TRANSCRIPTION_MODEL_NAMES = {
    "en": "English",
    "bn": "Bengali"
}
