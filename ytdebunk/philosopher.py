import google.generativeai as genai
import os, sys, logging
import ytdebunk.settings as settings
from ytdebunk.chunker import chunk_text
from dotenv import load_dotenv
load_dotenv()


def detect_logical_faults(transcription, 
                          key=None, 
                          verbose=False, 
                          language=settings.LANUAGE_DEFAULT,
                          logger=None):
    
    if logger is None:
        logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
        logger = logging.getLogger(__name__)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

    resolved_key = key or os.getenv("GEMINI_API_KEY") or os.getenv("GENAI_API_KEY")
    if not resolved_key:
        logger.error("[ytdebunk-analyzer] No Gemini API key provided or found in GEMINI_API_KEY / GENAI_API_KEY.")
        raise ValueError("Gemini API key is required for logical fault detection.")

    fault_detection_prompt = f"""
You are a {settings.TRANSCRIPTION_MODEL_NAMES[language]} language expert and a philosopher specializing in detecting logical flows, fallacies, bias, and irony in a {settings.TRANSCRIPTION_MODEL_NAMES[language]} speaker's content. 
Please be precise and critical while evaluating a piece of {settings.TRANSCRIPTION_MODEL_NAMES[language]} content from a {settings.TRANSCRIPTION_MODEL_NAMES[language]}-speaking YouTuber.

IMPORTANT:
1. Generate in {settings.TRANSCRIPTION_MODEL_NAMES[language]} only.
2. Keep the fallacy, bias, irony, and logical faults in the same order as they appear in the content.
3. Keep the summary concise and to the point and withing single large paragraph without showing point by point.

Here is the speaker's text:
"""

    genai.configure(api_key=resolved_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    chunks = chunk_text(transcription)
    refined_chunks = []

    logger.info(f"[ytdebunk-analyzer] Analyzing {len(chunks)} chunks of text...")
    for idx, chunk in enumerate(chunks):
        if verbose:
            logger.info(f"[ytdebunk-analyzer] Analyzing chunk {idx + 1} of {len(chunks)}")
        prompt = fault_detection_prompt + chunk
        try:
            response = model.generate_content(prompt)
            refined_chunks.append(response.text.strip())
        except Exception as e:
            logger.error(f"[ytdebunk-analyzer] Error while processing chunk {idx + 1}: {e}")
            refined_chunks.append(f"[ytdebunk-analyzer] Error processing chunk {idx + 1}")

    return " ".join(refined_chunks)
