import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()

def chunk_text(text, max_chars=3000):
    sentences = text.split("।")
    chunks, current_chunk = [], ""

    for sentence in sentences:
        # Prevent chunks from exceeding max_chars, even if they don't end with "।"
        if len(current_chunk) + len(sentence) + 1 <= max_chars:
            current_chunk += sentence + "।"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + "।"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

fault_detection_prompt = """
You are a Bangla language expert and a philosopher specializing in detecting logical flows, fallacies, bias, and irony in a Bangla speaker's content. Please be precise and critical while evaluating a piece of Bangla content from a Bangla-speaking YouTuber.

IMPORTANT:
1. Generate in Bangla only.
2. Keep the fallacy, bias, irony, and logical faults in the same order as they appear in the content.
3. Keep the summary concise and to the point and withing single large paragraph without showing point by point.

Here is the speaker's text:
"""

def detect_logical_faults(transcription, key=os.getenv("GENAI_API_KEY"), verbose=False):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    chunks = chunk_text(transcription)
    refined_chunks = []

    print(f"[ytdebunk-analyzer] Analyzing {len(chunks)} chunks of text...")
    for idx, chunk in enumerate(chunks):
        if verbose:
            print(f"[ytdebunk-analyzer] Analyzing chunk {idx + 1} of {len(chunks)}")
        prompt = fault_detection_prompt + chunk
        try:
            response = model.generate_content(prompt)
            refined_chunks.append(response.text.strip())
        except Exception as e:
            print(f"[ytdebunk-analyzer] Error while processing chunk {idx + 1}: {e}")
            refined_chunks.append(f"[ytdebunk-analyzer] Error processing chunk {idx + 1}")

    return " ".join(refined_chunks)