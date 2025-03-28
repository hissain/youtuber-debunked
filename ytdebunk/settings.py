OUTPUT_DIRECTORY = 'output'
AUDIO_FILE = OUTPUT_DIRECTORY + '/audio.mp3'
VIDEO_FILE = OUTPUT_DIRECTORY + '/video.mp4'
TRANSCRIPTION_FILE = OUTPUT_DIRECTORY + '/transcription.txt'
REFINED_TRANSCRIPTION_FILE = OUTPUT_DIRECTORY + '/refined_transcription.txt'
LOGICAL_FAULTS_FILE = OUTPUT_DIRECTORY + '/logical_faults.txt'

LANUAGE_DEFAULT = "en"

TRANSCRIPTION_MODELS = {
    "en": "openai/whisper-small",
    "bn": "bangla-speech-processing/BanglaASR"
}

TRANSCRIPTION_MODEL_NAMES = {
    "en": "English",
    "bn": "Bengali"
}
