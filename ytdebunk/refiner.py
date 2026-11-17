import google.generativeai as genai
import ytdebunk.settings as settings
from ytdebunk.chunker import chunk_text
import os, sys, logging

from dotenv import load_dotenv
load_dotenv()


def enhance_transcription(transcription, 
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
        logger.error("[ytdebunk-refiner] No Gemini API key provided or found in GEMINI_API_KEY / GENAI_API_KEY.")
        raise ValueError("Gemini API key is required for enhancement.")

    enchacement_prompt = f"""
You are a {settings.TRANSCRIPTION_MODEL_NAMES[language]} language expert. You have been asked to improve the following {settings.TRANSCRIPTION_MODEL_NAMES[language]} transcription by correcting errors and enhancing readability.

IMPORTANT:
1. Return only the transcription without any additional information or instructions.
2. Do not change the meaning of the transcription.
3. Do not add any new information to the transcription.
4. Do not remove any information from the transcription.

Here is the transcription:

"""

    genai.configure(api_key=resolved_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    chunks = chunk_text(transcription)
    refined_chunks = []

    logger.info(f"[ytdebunk-refiner] Refining {len(chunks)} chunks of text...")
    for idx, chunk in enumerate(chunks):
        if verbose:
            logger.info(f"[ytdebunk-refiner] Refining chunk no. {idx + 1}")
        prompt = enchacement_prompt + chunk
        response = model.generate_content(prompt)
        refined_chunks.append(response.text.strip())
    return " ".join(refined_chunks)
